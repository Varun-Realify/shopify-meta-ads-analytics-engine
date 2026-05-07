import os
import base64
import httpx
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

QB_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QB_API_BASE = "https://sandbox-quickbooks.api.intuit.com"


from core.database import get_database

class QuickBooksService:
    def __init__(self):
        self.client_id = os.getenv("QB_CLIENT_ID")
        self.client_secret = os.getenv("QB_CLIENT_SECRET")
        self.redirect_uri = os.getenv("QB_REDIRECT_URI")

    async def save_tokens(self, user_id: str, realm_id: str, access_token: str, refresh_token: str):
        from datetime import datetime, timezone
        db = get_database()
        await db.qb_tokens.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "realm_id": realm_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )

    async def get_tokens(self, user_id: str):
        db = get_database()
        return await db.qb_tokens.find_one({"user_id": user_id})

    def get_auth_url(self, user_id: str = "default"):
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "redirect_uri": self.redirect_uri,
            "state": user_id  # Use state to pass user_id through the OAuth flow
        }
        return f"{QB_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str):
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                QB_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
            )

            if response.status_code != 200:
                raise Exception(f"QB token error: {response.text}")

            return response.json()

    async def refresh_token(self, refresh_token: str):
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                QB_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )

            if response.status_code != 200:
                raise Exception(f"QB refresh error: {response.text}")

            return response.json()

    async def get_profit_loss(self, access_token, realm_id, start_date=None, end_date=None):
        params = {}
        if start_date: params["start_date"] = start_date
        if end_date:   params["end_date"]   = end_date

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QB_API_BASE}/v3/company/{realm_id}/reports/ProfitAndLoss",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                },
                params=params
            )

            if response.status_code != 200:
                raise Exception(f"QB API error: {response.text}")

            return response.json()


quickbooks_service = QuickBooksService()