import requests
import logging
from datetime import date
from services.shop_context import get_shop_data

logger = logging.getLogger(__name__)


def get_headers(token):
    return {"X-Shopify-Access-Token": token}


def get_base_url(shop):
    return f"https://{shop}/admin/api/2024-01"


def safe_get(url, headers):
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def get_all_products(shop: str):
    ctx = get_shop_data(shop)

    url = f"{get_base_url(ctx['shop'])}/products.json"
    data = safe_get(url, get_headers(ctx["token"]))

    return data.get("products", [])


def get_orders(shop: str, start_date: date, end_date: date):
    ctx = get_shop_data(shop)
    
    # Shopify ISO Format
    min_date = start_date.strftime("%Y-%m-%dT00:00:00Z")
    max_date = end_date.strftime("%Y-%m-%dT23:59:59Z")

    # status=any is critical to see all orders (not just open ones)
    url = f"{get_base_url(ctx['shop'])}/orders.json?status=any&created_at_min={min_date}&created_at_max={max_date}"
    
    print(f"🔗 FETCHING ORDERS: {url}")
    data = safe_get(url, get_headers(ctx["token"]))

    return data.get("orders", [])


def get_sales_by_product(shop: str, start_date: date, end_date: date):
    orders = get_orders(shop, start_date, end_date)

    sales = {}

    for order in orders:
        for item in order.get("line_items", []):
            pid = str(item["product_id"])

            if pid not in sales:
                sales[pid] = {
                    "product_id": pid,
                    "title": item.get("title"),
                    "units_sold": 0,
                    "revenue": 0
                }

            sales[pid]["units_sold"] += item["quantity"]
            sales[pid]["revenue"] += float(item["price"]) * item["quantity"]

    return sales


def get_intelligence_summary(shop: str):
    # For now, let's just get the last 30 days of data
    from datetime import date, timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    orders = get_orders(shop, start_date, end_date)
    
    total_orders = len(orders)
    net_revenue = sum(float(o.get("total_price", 0)) for o in orders)
    aov = net_revenue / total_orders if total_orders > 0 else 0
    
    # We can fake conversion rate for now or calculate if we had traffic data
    conversion_rate = 3.42 # Static for now
    
    return {
        "net_revenue": net_revenue,
        "total_orders": total_orders,
        "avg_order_value": aov,
        "conversion_rate": conversion_rate,
        "revenue_change": "+12%", # Placeholder
        "orders_change": "+5%", # Placeholder
        "aov_change": "+2%" # Placeholder
    }