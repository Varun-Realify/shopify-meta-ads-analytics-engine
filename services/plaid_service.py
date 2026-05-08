import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from cryptography.fernet import Fernet
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.config import Config
from core.database import get_database

logger = logging.getLogger(__name__)

PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


class PlaidService:
    def __init__(self):
        self.client_id = Config.PLAID_CLIENT_ID
        self.secret = Config.PLAID_SECRET
        self.env = Config.PLAID_ENV or "sandbox"
        self.base_url = PLAID_ENV_URLS.get(self.env, PLAID_ENV_URLS["sandbox"])

        if not Config.PLAID_ENCRYPTION_KEY:
            raise Exception("PLAID_ENCRYPTION_KEY is missing in .env")

        self.fernet = Fernet(Config.PLAID_ENCRYPTION_KEY.encode())

    # ── helpers ───────────────────────────────────────────────────────────────

    def _db(self) -> AsyncIOMotorDatabase:
        """Always returns the live Motor database instance."""
        database = get_database()
        if database is None:
            raise RuntimeError("MongoDB is not connected yet")
        return database

    def _encrypt_token(self, token: str) -> str:
        return self.fernet.encrypt(token.encode()).decode()

    def _decrypt_token(self, encrypted_token: str) -> str:
        return self.fernet.decrypt(encrypted_token.encode()).decode()

    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "client_id": self.client_id,
            "secret": self.secret,
            **data,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

        if response.status_code >= 400:
            logger.error(f"Plaid API error {response.status_code}: {response.text}")
            raise Exception(f"Plaid API error {response.status_code}: {response.text}")

        return response.json()

    # ── core methods ──────────────────────────────────────────────────────────

    async def create_link_token(self, user_id: str) -> Dict[str, Any]:
        response = await self._post("/link/token/create", {
            "user": {"client_user_id": user_id},
            "client_name": Config.PLAID_CLIENT_NAME,
            "products": Config.PLAID_PRODUCTS,
            "country_codes": Config.PLAID_COUNTRY_CODES,
            "language": Config.PLAID_LANGUAGE,
        })

        return {
            "link_token": response.get("link_token"),
            "expiration": response.get("expiration"),
            "request_id": response.get("request_id"),
        }

    async def exchange_and_store(self, user_id: str, public_token: str) -> Dict[str, Any]:
        exchange = await self._post("/item/public_token/exchange", {
            "public_token": public_token,
        })

        access_token = exchange["access_token"]
        item_id = exchange["item_id"]
        encrypted_access_token = self._encrypt_token(access_token)

        institution_id = None
        institution_name = None

        try:
            item_resp = await self._post("/item/get", {
                "access_token": access_token,
            })

            institution_id = item_resp.get("item", {}).get("institution_id")

            if institution_id:
                institution_resp = await self._post("/institutions/get_by_id", {
                    "institution_id": institution_id,
                    "country_codes": Config.PLAID_COUNTRY_CODES,
                })
                institution_name = institution_resp.get("institution", {}).get("name")

        except Exception as e:
            logger.warning(f"Could not fetch Plaid institution info: {e}")

        now = datetime.utcnow()

        await self._db().plaid_connections.update_one(
            {
                "user_id": user_id,
                "item_id": item_id,
            },
            {
                "$set": {
                    "access_token": encrypted_access_token,
                    "institution_id": institution_id,
                    "institution_name": institution_name,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "item_id": item_id,
                    "created_at": now,
                },
            },
            upsert=True,
        )

        return {
            "success": True,
            "item_id": item_id,
            "institution_id": institution_id,
            "institution_name": institution_name,
            "message": "Bank account linked successfully",
        }

    async def _get_connection_doc(
        self,
        user_id: str,
        item_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        query = {"user_id": user_id}

        if item_id:
            query["item_id"] = item_id

        return await self._db().plaid_connections.find_one(
            query,
            sort=[("created_at", -1)],
        )

    async def get_accounts_for_user(
        self,
        user_id: str,
        item_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        doc = await self._get_connection_doc(user_id, item_id)

        if not doc:
            raise Exception("No Plaid connection for this user")

        access_token = self._decrypt_token(doc["access_token"])

        response = await self._post("/accounts/get", {
            "access_token": access_token,
        })

        return {
            "user_id": user_id,
            "item_id": doc["item_id"],
            "institution_name": doc.get("institution_name"),
            "accounts": response.get("accounts", []),
        }

    async def get_transactions_for_user(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        item_id: Optional[str] = None,
        count: int = 500,
        offset: int = 0,
    ) -> Dict[str, Any]:
        doc = await self._get_connection_doc(user_id, item_id)

        if not doc:
            raise Exception("No Plaid connection for this user")

        access_token = self._decrypt_token(doc["access_token"])

        response = await self._post("/transactions/get", {
            "access_token": access_token,
            "start_date": start_date,
            "end_date": end_date,
            "options": {
                "count": count,
                "offset": offset,
            },
        })

        return {
            **response,
            "user_id": user_id,
            "item_id": doc["item_id"],
            "institution_name": doc.get("institution_name"),
        }

    async def get_connections_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self._db().plaid_connections.find(
            {"user_id": user_id},
            sort=[("created_at", -1)],
        )

        docs = await cursor.to_list(length=100)

        return [
            {
                "item_id": d["item_id"],
                "institution_id": d.get("institution_id"),
                "institution_name": d.get("institution_name"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
            }
            for d in docs
        ]

    async def create_sandbox_token_for_user(
        self,
        user_id: str,
        institution_id: str = "ins_109508",
    ) -> Dict[str, Any]:
        if self.env != "sandbox":
            raise Exception("Sandbox connect is only allowed when PLAID_ENV=sandbox")

        sandbox = await self._post("/sandbox/public_token/create", {
            "institution_id": institution_id,
            "initial_products": Config.PLAID_PRODUCTS,
            "options": {
                "override_username": "user_good",
                "override_password": "pass_good",
            },
        })

        public_token = sandbox["public_token"]
        return await self.exchange_and_store(user_id, public_token)

    async def test_connection(self) -> Dict[str, Any]:
        try:
            result = await self.create_link_token("health_check_user")

            return {
                "connected": True,
                "environment": self.env,
                "request_id": result.get("request_id"),
            }

        except Exception as e:
            return {
                "connected": False,
                "environment": self.env,
                "error": str(e),
            }


plaid_service = PlaidService()