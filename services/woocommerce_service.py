import httpx
import logging
import asyncio
from typing import List, Dict, Any
from datetime import date
from core.config import Config

logger = logging.getLogger(__name__)

class WooCommerceService:
    def __init__(self):
        self.base_url = f"{Config.WOO_URL.rstrip('/')}/wp-json/wc/v3"
        self.auth = (Config.WOO_CONSUMER_KEY, Config.WOO_CONSUMER_SECRET)

    async def _safe_get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{endpoint}",
                    params=params,
                    auth=self.auth,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"WooCommerce API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"WooCommerce API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"WooCommerce connection error: {str(e)}")
                raise

    async def test_connection(self) -> Dict[str, Any]:
        try:
            # Simple call to verify credentials and URL
            data = await self._safe_get("system_status")
            return {
                "connected": True,
                "url": Config.WOO_URL,
                "version": data.get("environment", {}).get("version", "unknown")
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def get_all_products(self) -> List[Dict[str, Any]]:
        logger.info("Fetching WooCommerce products...")
        try:
            products = await self._safe_get("products", params={"per_page": 100})
            result = []
            for p in products:
                # Normalizing to a similar structure as Shopify
                result.append({
                    "id": str(p["id"]),
                    "title": p["name"],
                    "vendor": "WooCommerce",
                    "product_type": "Variable" if p["type"] == "variable" else "Simple",
                    "selling_price": float(p.get("price", 0) or 0),
                    "cost_price": 0.0, # WooCommerce doesn't have cost price in core usually
                    "stock": p.get("stock_quantity") or 0
                })
            return result
        except Exception as e:
            logger.error(f"Error fetching WooCommerce products: {e}")
            return []

    async def get_orders(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        logger.info(f"Fetching WooCommerce orders from {start_date} to {end_date}...")
        try:
            # WooCommerce uses ISO8601
            params = {
                "after": f"{start_date}T00:00:00",
                "before": f"{end_date}T23:59:59",
                "per_page": 100
            }
            orders = await self._safe_get("orders", params=params)
            return orders
        except Exception as e:
            logger.error(f"Error fetching WooCommerce orders: {e}")
            return []

    async def get_sales_by_product(self, start_date: date, end_date: date) -> Dict[str, Any]:
        orders = await self.get_orders(start_date, end_date)
        sales = {}
        for order in orders:
            if order.get("status") not in ["processing", "completed"]:
                continue
            
            order_date = order["date_created"][:10]
            for item in order.get("line_items", []):
                pid = str(item["product_id"])
                qty = item["quantity"]
                revenue = float(item["total"])

                if pid not in sales:
                    sales[pid] = {
                        "product_id": pid,
                        "title": item.get("name", "Unknown"),
                        "units_sold": 0,
                        "revenue": 0.0,
                        "order_count": 0,
                        "dates": []
                    }
                sales[pid]["units_sold"] += qty
                sales[pid]["revenue"] += revenue
                sales[pid]["order_count"] += 1
                sales[pid]["dates"].append(order_date)
        return sales

    async def get_daily_sales_timeseries_all(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        orders = await self.get_orders(start_date, end_date)
        daily = {}
        for order in orders:
            if order.get("status") not in ["processing", "completed"]:
                continue
            order_date = order["date_created"][:10]
            revenue = float(order["total"])
            
            if order_date not in daily:
                daily[order_date] = {"date": order_date, "units_sold": 0, "revenue": 0.0}
            
            daily[order_date]["revenue"] += revenue
            for item in order.get("line_items", []):
                daily[order_date]["units_sold"] += item["quantity"]
        
        return sorted(daily.values(), key=lambda x: x["date"])

woocommerce_service = WooCommerceService()
