import httpx
import logging
from typing import Dict, Any
from core.config import Config

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        self.secret = Config.STRIPE_SECRET
        self.base_url = "https://api.stripe.com/v1"

    async def _post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a POST request to Stripe API using form-urlencoded data"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    data=data,
                    headers={
                        "Authorization": f"Bearer {self.secret}"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Stripe API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Stripe API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Stripe connection error: {str(e)}")
                raise

    async def create_checkout_session(
        self, 
        product_name: str, 
        amount: int, 
        currency: str = "usd", 
        success_url: str = "http://localhost:8000/success", 
        cancel_url: str = "http://localhost:8000/cancel"
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session"""
        try:
            # For Stripe form-urlencoded arrays/dicts, we flatten the keys
            data = {
                "payment_method_types[0]": "card",
                "line_items[0][price_data][currency]": currency,
                "line_items[0][price_data][product_data][name]": product_name,
                "line_items[0][price_data][unit_amount]": amount, # Amount in cents
                "line_items[0][quantity]": 1,
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url
            }
            response = await self._post("/checkout/sessions", data)
            return {
                "checkout_url": response.get("url"),
                "session_id": response.get("id"),
                "payment_status": response.get("payment_status")
            }
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {e}")
            raise

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a checkout session"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/checkout/sessions/{session_id}",
                    headers={
                        "Authorization": f"Bearer {self.secret}"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "id": data.get("id"),
                    "payment_status": data.get("payment_status"),
                    "status": data.get("status"),
                    "customer_email": data.get("customer_details", {}).get("email") if data.get("customer_details") else None
                }
            except httpx.HTTPStatusError as e:
                logger.error(f"Stripe API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Stripe API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Stripe connection error: {str(e)}")
                raise

# Singleton instance
stripe_service = StripeService()
