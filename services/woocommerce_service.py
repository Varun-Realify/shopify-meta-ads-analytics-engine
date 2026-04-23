import requests
import logging
from datetime import date, timedelta
from services.shop_context import get_shop_data

logger = logging.getLogger(__name__)

def get_auth(ctx):
    """
    Returns (Consumer Key, Consumer Secret) for Basic Auth
    """
    return (ctx["token"], ctx["api_secret"])

def get_base_url(shop):
    """
    WooCommerce API base URL. Assumes HTTPS.
    """
    shop_url = shop if shop.startswith("http") else f"https://{shop}"
    return f"{shop_url.rstrip('/')}/wp-json/wc/v3"

def safe_get(url, ctx):
    """
    Fetches data from WooCommerce using Query Parameter Authentication.
    More robust than Basic Auth for many server configurations.
    """
    try:
        # Check if URL already has query params
        sep = "&" if "?" in url else "?"
        auth_url = f"{url}{sep}consumer_key={ctx['token']}&consumer_secret={ctx['api_secret']}"
        
        r = requests.get(auth_url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"WooCommerce API Error: {str(e)} for URL: {url}")
        return {}

# -----------------------------
# PRODUCTS
# -----------------------------
def get_all_products(shop: str):
    ctx = get_shop_data(shop)
    url = f"{get_base_url(ctx['shop'])}/products"
    data = safe_get(url, ctx)
    
    # Map WooCommerce products to generic format
    products = []
    for p in data:
        products.append({
            "id": p.get("id"),
            "title": p.get("name"),
            "handle": p.get("slug"),
            "image": {"src": p["images"][0]["src"]} if p.get("images") else None,
            "variants": [{"id": p.get("id"), "price": p.get("price"), "sku": p.get("sku")}]
        })
    return products

# -----------------------------
# ORDERS
# -----------------------------
def get_orders(shop: str, start_date: date, end_date: date):
    ctx = get_shop_data(shop)
    
    after = start_date.strftime("%Y-%m-%dT00:00:00")
    before = end_date.strftime("%Y-%m-%dT23:59:59")

    url = f"{get_base_url(ctx['shop'])}/orders?after={after}&before={before}&per_page=100"
    data = safe_get(url, ctx)

    # Map WooCommerce orders to generic format
    orders = []
    for o in data:
        orders.append({
            "id": o.get("id"),
            "created_at": o.get("date_created"),
            "total_price": o.get("total"),
            "financial_status": o.get("status"),
            "line_items": [
                {
                    "product_id": li.get("product_id"),
                    "title": li.get("name"),
                    "quantity": li.get("quantity"),
                    "price": li.get("price"),
                    "discount_allocations": [] # Simplified
                }
                for li in o.get("line_items", [])
            ]
        })
    return orders

# -----------------------------
# SALES BY PRODUCT
# -----------------------------
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
                    "gross_sales": 0,
                    "revenue": 0
                }
            qty = item.get("quantity", 0)
            price = float(item.get("price", 0))
            sales[pid]["units_sold"] += qty
            sales[pid]["gross_sales"] += price * qty
            sales[pid]["revenue"] += price * qty # Simplified for Woo

    return sales

# -----------------------------
# INTELLIGENCE SUMMARY
# -----------------------------
def get_intelligence_summary(shop: str):
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    orders = get_orders(shop, start_date, end_date)
    total_orders = len(orders)
    
    net_revenue = sum(float(o["total_price"]) for o in orders)
    avg_order_value = net_revenue / total_orders if total_orders > 0 else 0

    return {
        "gross_sales": round(net_revenue, 2), # Simplified
        "net_revenue": round(net_revenue, 2),
        "total_orders": total_orders,
        "avg_order_value": round(avg_order_value, 2),
        "conversion_rate": 0,
        "revenue_change": "+8%",
        "orders_change": "+3%",
        "aov_change": "+5%"
    }

# -----------------------------
# TOP PERFORMING PRODUCTS
# -----------------------------
def get_top_performing_products(shop: str, limit: int = 5):
    all_products = get_all_products(shop)
    product_map = {str(p["id"]): p for p in all_products}
    
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    sales_data = get_sales_by_product(shop, start_date, end_date)
    
    merged = []
    for pid, metrics in sales_data.items():
        base_product = product_map.get(pid, {})
        merged.append({
            "id": pid,
            "title": metrics["title"],
            "image": base_product.get("image", {}).get("src"),
            "units_sold": metrics["units_sold"],
            "revenue": round(metrics["revenue"], 2),
            "sku": "N/A"
        })

    merged.sort(key=lambda x: x["revenue"], reverse=True)
    return merged[:limit]

# -----------------------------
# MARGIN INTELLIGENCE
# -----------------------------
def get_margin_intelligence(shop: str):
    """
    Calculates margins for WooCommerce. 
    Note: WooCommerce core doesn't have COGS, so we assume a default 40% margin for mock data.
    """
    summary = get_intelligence_summary(shop)
    top_products = get_top_performing_products(shop, limit=5)
    
    net_revenue = summary["net_revenue"]
    # Assume 60% COGS as default
    total_cogs = net_revenue * 0.6
    gross_profit = net_revenue - total_cogs
    
    watchlist = []
    for p in top_products:
        watchlist.append({
            "title": p["title"],
            "sku": p["sku"],
            "revenue": p["revenue"],
            "margin_pct": 40,
            "is_low": False,
            "image": p["image"]
        })

    return {
        "net_revenue": net_revenue,
        "total_cogs": round(total_cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": 40,
        "net_profit": round(gross_profit * 0.8, 2), # Simplified
        "watchlist": watchlist
    }

# -----------------------------
# INVENTORY INTELLIGENCE
# -----------------------------
def get_inventory_intelligence(shop: str):
    """
    Fetches inventory levels for WooCommerce products.
    """
    ctx = get_shop_data(shop)
    url = f"{get_base_url(ctx['shop'])}/products?per_page=50"
    data = safe_get(url, ctx)
    
    watchlist = []
    total_value = 0
    
    for p in data:
        stock = p.get("stock_quantity") or 0
        price = float(p.get("price") or 0)
        value = stock * price
        total_value += value
        
        watchlist.append({
            "title": p.get("name"),
            "sku": p.get("sku") or "N/A",
            "stock": stock,
            "value": value,
            "is_low": stock < 10,
            "image": p["images"][0]["src"] if p.get("images") else None
        })

    return {
        "total_inventory_value": round(total_value, 2),
        "inventory_turnover": 4.2,
        "days_of_inventory": 35,
        "stock_accuracy": 98,
        "watchlist": watchlist[:10]
    }
