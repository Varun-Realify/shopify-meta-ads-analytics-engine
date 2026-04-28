import httpx
import logging
import base64
from typing import Dict, Any, List
from core.config import Config

logger = logging.getLogger(__name__)

# Plaid API base URLs for different environments
PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}

class PlaidService:
    def __init__(self):
        self.client_id = Config.PLAID_CLIENT_ID
        self.secret = Config.PLAID_SECRET
        self.env = Config.PLAID_ENV or "sandbox"
        self.base_url = PLAID_ENV_URLS.get(self.env, PLAID_ENV_URLS["sandbox"])

    def _get_auth(self) -> str:
        """Generate Basic auth header from client_id and secret"""
        credentials = f"{self.client_id}:{self.secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to Plaid API"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": self._get_auth()
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Plaid API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Plaid API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Plaid connection error: {str(e)}")
                raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test Plaid connection with sandbox credentials"""
        try:
            # Use /item/create to test credentials
            response = await self._post("/item/create", {
                "client_id": self.client_id,
                "secret": self.secret,
                "country_codes": ["US"],
                "products": ["transactions"]
            })
            return {
                "connected": True,
                "environment": self.env,
                "item_id": response.get("item", {}).get("item_id"),
                "request_id": response.get("request_id")
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def create_link_token(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Create a Link token for Plaid Link initialization"""
        try:
            response = await self._post("/link/token/create", {
                "client_id": self.client_id,
                "secret": self.secret,
                "user": {"client_user_id": user_id},
                "client_name": "Shopify Meta Ads Analytics",
                "products": ["transactions"],
                "country_codes": ["US"],
                "language": "en"
            })
            return {
                "link_token": response.get("link_token"),
                "expiration": response.get("expiration"),
                "request_id": response.get("request_id")
            }
        except Exception as e:
            logger.error(f"Error creating Link token: {e}")
            raise

    async def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """Exchange public token for access token"""
        try:
            response = await self._post("/item/public_token/exchange", {
                "client_id": self.client_id,
                "secret": self.secret,
                "public_token": public_token
            })
            return {
                "access_token": response.get("access_token"),
                "item_id": response.get("item_id"),
                "request_id": response.get("request_id")
            }
        except Exception as e:
            logger.error(f"Error exchanging public token: {e}")
            raise

    async def get_transactions(self, access_token: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch transactions for a given date range"""
        try:
            response = await self._post("/transactions/get", {
                "client_id": self.client_id,
                "secret": self.secret,
                "access_token": access_token,
                "start_date": start_date,
                "end_date": end_date,
                "options": {
                    "count": 500,
                    "offset": 0
                }
            })
            return response
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            raise

    async def get_accounts(self, access_token: str) -> Dict[str, Any]:
        """Fetch accounts associated with an access token"""
        try:
            response = await self._post("/accounts/get", {
                "client_id": self.client_id,
                "secret": self.secret,
                "access_token": access_token
            })
            return response
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}")
            raise

    async def get_institutions(self, institution_id: str) -> Dict[str, Any]:
        """Fetch institution details by ID"""
        try:
            response = await self._post("/institutions/get_by_id", {
                "client_id": self.client_id,
                "secret": self.secret,
                "institution_id": institution_id,
                "country_codes": ["US"],
                "options": {
                    "include_optional_metadata": True
                }
            })
            return response
        except Exception as e:
            logger.error(f"Error fetching institution: {e}")
            raise

    async def get_item(self, access_token: str) -> Dict[str, Any]:
        """Get item details and status"""
        try:
            response = await self._post("/item/get", {
                "client_id": self.client_id,
                "secret": self.secret,
                "access_token": access_token
            })
            return response
        except Exception as e:
            logger.error(f"Error fetching item: {e}")
            raise


# Singleton instance
plaid_service = PlaidService()