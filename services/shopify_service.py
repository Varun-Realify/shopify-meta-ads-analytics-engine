import httpx
import logging
import asyncio
import time
from datetime import date
from core.config import Config

logger = logging.getLogger(__name__)

BASE_URL = f"https://{Config.SHOPIFY_STORE_NAME}/admin/api/{Config.SHOPIFY_API_VERSION}"
HEADERS  = {"X-Shopify-Access-Token": Config.SHOPIFY_ACCESS_TOKEN}


async def safe_get(url, params=None, retries=3):
    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                r = await client.get(url, headers=HEADERS, params=params, timeout=15.0)
                if r.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if r.status_code == 401:
                    raise Exception("Shopify: Invalid access token (401)")
                if r.status_code == 403:
                    raise Exception("Shopify: Forbidden — check API scopes (403)")
                if r.status_code == 404:
                    return {}
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError as e:
                if attempt == retries - 1:
                    raise Exception(f"Shopify API error: {e}")
                await asyncio.sleep(2 ** attempt)
    return {}


async def test_connection() -> dict:
    try:
        data = await safe_get(f"{BASE_URL}/shop.json")
        shop = data.get("shop", {})
        return {
            "connected": True,
            "store":     shop.get("name", ""),
            "domain":    shop.get("domain", ""),
            "currency":  shop.get("currency", ""),
            "email":     shop.get("email", ""),
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def get_all_products() -> list:
    logger.info("Fetching Shopify products...")
    data     = await safe_get(f"{BASE_URL}/products.json", params={"limit": 250})
    products = data.get("products", [])
    result   = []

    for p in products:
        variant     = p["variants"][0] if p["variants"] else {}
        sell_price  = float(variant.get("price", 0))
        inv_item_id = variant.get("inventory_item_id")
        cost_price  = await _get_product_cost(inv_item_id) if inv_item_id else 0.0

        result.append({
            "id":            str(p["id"]),
            "title":         p["title"],
            "vendor":        p.get("vendor", ""),
            "product_type":  p.get("product_type", ""),
            "selling_price": sell_price,
            "cost_price":    cost_price,
            "variant_id":    str(variant.get("id", "")),
            "stock":         variant.get("inventory_quantity", 0),
        })

    logger.info(f"Found {len(result)} products")
    return result


async def _get_product_cost(inventory_item_id) -> float:
    try:
        data = await safe_get(f"{BASE_URL}/inventory_items/{inventory_item_id}.json")
        cost = data.get("inventory_item", {}).get("cost")
        return float(cost) if cost else 0.0
    except Exception:
        return 0.0


async def get_orders(start_date: date, end_date: date) -> list:
    logger.info(f"Fetching orders {start_date} → {end_date}...")
    all_orders = []
    url        = f"{BASE_URL}/orders.json"
    params     = {
        "status":         "any",
        "created_at_min": f"{start_date}T00:00:00Z",
        "created_at_max": f"{end_date}T23:59:59Z",
        "limit":          250,
    }

    async with httpx.AsyncClient() as client:
        while url:
            r = await client.get(url, headers=HEADERS, params=params, timeout=15.0)
            r.raise_for_status()
            data = r.json()
            orders = data.get("orders", [])
            all_orders.extend(orders)
            
            # Link header handling for pagination
            link = r.headers.get("Link")
            if link and 'rel="next"' in link:
                url = link.split(';')[0].strip('<>')
                params = {}
            else:
                url = None

    logger.info(f"Retrieved {len(all_orders)} total orders")
    return all_orders


async def get_realtime_orders(minutes=1440):
    """
    Retrieves recent orders from the last 'minutes' to cross-check with Ads.
    """
    from datetime import datetime, timedelta
    start_time = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
    params = {
        "status": "any",
        "created_at_min": f"{start_time}Z",
        "limit": 50
    }
    data = await safe_get(f"{BASE_URL}/orders.json", params=params)
    return data.get("orders", [])


async def get_sales_by_product(start_date: date, end_date: date) -> dict:
    orders = await get_orders(start_date, end_date)
    sales  = {}

    for order in orders:
        if order.get("financial_status") not in ["paid", "partially_paid"]:
            continue
        for item in order.get("line_items", []):
            pid     = str(item["product_id"])
            qty     = item["quantity"]
            revenue = float(item["price"]) * qty

            if pid not in sales:
                sales[pid] = {
                    "product_id":  pid,
                    "title":       item.get("title", "Unknown"),
                    "units_sold":  0,
                    "revenue":     0.0,
                    "order_count": 0,
                    "dates":       [],
                }
            sales[pid]["units_sold"]  += qty
            sales[pid]["revenue"]     += revenue
            sales[pid]["order_count"] += 1
            sales[pid]["dates"].append(order["created_at"][:10])

    return sales


async def get_daily_sales_timeseries(product_id: str, start_date: date, end_date: date) -> list:
    orders = await get_orders(start_date, end_date)
    daily  = {}

    for order in orders:
        if order.get("financial_status") not in ["paid", "partially_paid"]:
            continue
        order_date = order["created_at"][:10]
        for item in order.get("line_items", []):
            if str(item["product_id"]) != str(product_id):
                continue
            qty     = item["quantity"]
            revenue = float(item["price"]) * qty
            if order_date not in daily:
                daily[order_date] = {"date": order_date, "units_sold": 0, "revenue": 0.0}
            daily[order_date]["units_sold"] += qty
            daily[order_date]["revenue"]    += revenue

    return sorted(daily.values(), key=lambda x: x["date"])


async def get_daily_sales_timeseries_all(start_date: date, end_date: date) -> list:
    orders = await get_orders(start_date, end_date)
    daily  = {}

    for order in orders:
        if order.get("financial_status") not in ["paid", "partially_paid"]:
            continue
        order_date = order["created_at"][:10]
        for item in order.get("line_items", []):
            qty     = item["quantity"]
            revenue = float(item["price"]) * qty
            if order_date not in daily:
                daily[order_date] = {"date": order_date, "units_sold": 0, "revenue": 0.0}
            daily[order_date]["units_sold"] += qty
            daily[order_date]["revenue"]    += revenue

    return sorted(daily.values(), key=lambda x: x["date"])
