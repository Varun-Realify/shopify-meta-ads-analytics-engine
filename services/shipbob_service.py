import httpx
import logging
from typing import Dict, Any, List
from core.config import Config

logger = logging.getLogger(__name__)

SHIPBOB_BASE_URL = "https://api.shipbob.com/2026-01"

class ShipBobService:
    def __init__(self):
        self.api_token = Config.SHIPBOB_API_TOKEN
        self.base_url = SHIPBOB_BASE_URL

    async def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{endpoint}",
                    headers=headers,
                    params=params,
                    timeout=20.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"ShipBob API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"ShipBob API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"ShipBob connection error: {str(e)}")
                raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection by fetching inventory levels with a limit of 1"""
        try:
            await self._get("inventory-level", params={"limit": 1})
            return {"connected": True}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def get_inventory(self) -> List[Dict[str, Any]]:
        """Fetch all inventory levels"""
        try:
            data = await self._get("inventory-level")
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Error fetching ShipBob inventory: {e}")
            return []

    async def get_orders(self) -> List[Dict[str, Any]]:
        """Fetch recent orders"""
        try:
            data = await self._get("order")
            return data # ShipBob order endpoint usually returns a list directly or wrapped
        except Exception as e:
            logger.error(f"Error fetching ShipBob orders: {e}")
            return []

shipbob_service = ShipBobService()
