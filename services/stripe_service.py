import httpx
import logging
from datetime import datetime
from typing import Dict, Any, List
from core.config import Config
from core.database import db

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        # STRIPE_SECRET and STRIPE_CLIENT_ID must be in your Config class
        self.secret_key = getattr(Config, "STRIPE_SECRET", None)
        self.client_id = getattr(Config, "STRIPE_CLIENT_ID", None)
        self.base_url = "https://api.stripe.com/v1"

    async def exchange_token_and_save(self, code: str, internal_user_id: str):
        """Phase 1: Exchange temporary code for permanent access token"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://connect.stripe.com/oauth/token",
                data={
                    "client_secret": self.secret_key,
                    "code": code,
                    "grant_type": "authorization_code"
                }
            )
            data = response.json()
            
            if response.status_code != 200:
                # THIS LINE WILL SHOW THE ERROR IN YOUR TERMINAL
                print(f"STRIPE ERROR: {data}") 
                raise Exception(data.get("error_description", "Stripe exchange failed"))

            print(f"STRIPE SUCCESS RESPONSE: {data}")
            seller_data = {
                "user_id": internal_user_id,
                "stripe_user_id": data.get("stripe_user_id", "missing_user_id"),
                "access_token": data.get("access_token", "missing_token"),
                "connected_at": datetime.utcnow().isoformat(),
                "stripe_raw_response": data
            }

            try:
                await db.db.stripe_sellers.update_one(
                    {"user_id": internal_user_id},
                    {"$set": seller_data},
                    upsert=True
                )
                return seller_data
            except Exception as e:
                # THIS LINE WILL SHOW IF MONGODB IS BLOCKING YOU
                print(f"DATABASE ERROR: {e}")
                raise Exception("Failed to save to MongoDB")

    async def get_seller_payment_data(self, internal_user_id: str) -> List[Dict[str, Any]]:
        """Phase 2: Use stored token to fetch live payment history[cite: 1]"""
        # 1. Retrieve token from MongoDB[cite: 1]
        seller = await db.db.stripe_sellers.find_one({"user_id": internal_user_id})
        if not seller:
            raise Exception("Seller not connected to Stripe")
        
        # 2. Call Stripe using the seller's specific token[cite: 1]
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {seller['access_token']}"}
            
            response = await client.get(
                f"{self.base_url}/charges", 
                headers=headers,
                params={"limit": 20} 
            )
            
            if response.status_code != 200:
                logger.error(f"Stripe History Error: {response.text}")
                return []

            charges = response.json().get("data", [])
            
            # Format data for the professional dashboard[cite: 1]
            return [{
                "id": c.get("id"),
                "amount": c.get("amount") / 100, # Cents to Dollars
                "currency": c.get("currency", "").upper(),
                "receipt": c.get("receipt_url"), 
                "status": c.get("status"),
                "created": datetime.fromtimestamp(c.get("created")).strftime('%Y-%m-%d %H:%M:%S')
            } for c in charges]

stripe_service = StripeService()