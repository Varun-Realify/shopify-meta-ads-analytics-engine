import httpx
import logging
from core.config import Config

logger = logging.getLogger(__name__)

BASE_URL = f"{Config.WOO_URL}/wp-json/wc/v3"
AUTH = (Config.WOO_CONSUMER_KEY or "", Config.WOO_CONSUMER_SECRET or "")

async def test_connection() -> dict:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BASE_URL}/system_status", auth=AUTH, timeout=15)
            r.raise_for_status()
            data = r.json()
            return {
                "connected": True,
                "url": Config.WOO_URL,
                "environment": data.get("environment", {})
            }
    except Exception as e:
        logger.error(f"WooCommerce connection error: {e}")
        return {"connected": False, "error": str(e)}

async def get_all_products() -> list:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BASE_URL}/products", auth=AUTH, params={"per_page": 100}, timeout=15)
            r.raise_for_status()
            products = r.json()
            return [
                {
                    "id": str(p["id"]),
                    "title": p["name"],
                    "vendor": "WooCommerce",
                    "product_type": "Variable" if p.get("variations") else "Simple",
                    "selling_price": float(p.get("price", 0) or 0),
                    "cost_price": float(p.get("regular_price", 0) or 0) * 0.7, # Mock COGS
                    "stock": p.get("stock_quantity") or 0
                }
                for p in products
            ]
    except Exception as e:
        logger.error(f"WooCommerce products error: {e}")
        return []

async def get_orders(start_date=None, end_date=None) -> list:
    params = {"per_page": 100}
    if start_date:
        params["after"] = f"{start_date}T00:00:00"
    if end_date:
        params["before"] = f"{end_date}T23:59:59"

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BASE_URL}/orders", auth=AUTH, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"WooCommerce orders error: {e}")
        return []
