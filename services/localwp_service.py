import httpx
import logging
from typing import List, Dict, Any
from datetime import date
from core.config import Config

logger = logging.getLogger(__name__)

class LocalWPService:
    def __init__(self):
        # LocalWP often needs index.php if pretty permalinks are disabled
        self.base_url = f"{Config.LOCALWP_URL.rstrip('/')}/index.php/wp-json/wc/v3"
        self.consumer_key = Config.LOCALWP_CONSUMER_KEY
        self.consumer_secret = Config.LOCALWP_CONSUMER_SECRET
        self.live_username = Config.LOCALWP_LIVE_USERNAME
        self.live_password = Config.LOCALWP_LIVE_PASSWORD

    async def _safe_get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        if params is None:
            params = {}
        
        # When using Live Link Basic Auth, WooCommerce keys MUST be in query params
        params.update({
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret
        })

        async with httpx.AsyncClient() as client:
            try:
                # Basic Auth for the Live Link (site-level protection)
                auth = httpx.BasicAuth(self.live_username, self.live_password) if self.live_username else None
                
                response = await client.get(
                    f"{self.base_url}/{endpoint}",
                    params=params,
                    auth=auth,
                    timeout=30.0
                )
                
                # If 404, maybe retry without index.php (optional, but focusing on what worked in diagnosis)
                if response.status_code == 404 and "/index.php/" in self.base_url:
                    alt_url = self.base_url.replace("/index.php/", "/")
                    logger.info(f"Retrying LocalWP at {alt_url}...")
                    response = await client.get(
                        f"{alt_url}/{endpoint}",
                        params=params,
                        auth=auth,
                        timeout=30.0
                    )

                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"LocalWP API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"LocalWP API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"LocalWP connection error: {str(e)}")
                raise

    async def test_connection(self) -> Dict[str, Any]:
        try:
            data = await self._safe_get("system_status")
            return {
                "connected": True,
                "url": Config.LOCALWP_URL,
                "version": data.get("environment", {}).get("version", "unknown"),
                "method": "Double Basic Auth (Live Link)"
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def get_all_products(self) -> List[Dict[str, Any]]:
        logger.info("Fetching LocalWP products...")
        try:
            products = await self._safe_get("products", params={"per_page": 100})
            result = []
            for p in products:
                result.append({
                    "id": str(p["id"]),
                    "title": p["name"],
                    "vendor": "LocalWP",
                    "product_type": "Variable" if p["type"] == "variable" else "Simple",
                    "selling_price": float(p.get("price", 0) or 0),
                    "cost_price": 0.0,
                    "stock": p.get("stock_quantity") or 0
                })
            return result
        except Exception as e:
            logger.error(f"Error fetching LocalWP products: {e}")
            return []

    async def get_orders(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        logger.info(f"Fetching LocalWP orders from {start_date} to {end_date}...")
        try:
            params = {
                "after": f"{start_date}T00:00:00",
                "before": f"{end_date}T23:59:59",
                "per_page": 100
            }
            orders = await self._safe_get("orders", params=params)
            return orders
        except Exception as e:
            logger.error(f"Error fetching LocalWP orders: {e}")
            return []

localwp_service = LocalWPService()
