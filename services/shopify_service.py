# import requests
# import logging
# from datetime import date
# from services.shop_context import get_shop_data

# logger = logging.getLogger(__name__)


# def get_headers(token):
#     return {"X-Shopify-Access-Token": token}


# def get_base_url(shop):
#     return f"https://{shop}/admin/api/2024-01"


# def safe_get(url, headers):
#     r = requests.get(url, headers=headers)
#     r.raise_for_status()
#     return r.json()


# def get_all_products(shop: str):
#     ctx = get_shop_data(shop)

#     url = f"{get_base_url(ctx['shop'])}/products.json"
#     data = safe_get(url, get_headers(ctx["token"]))

#     return data.get("products", [])


# def get_orders(shop: str, start_date: date, end_date: date):
#     ctx = get_shop_data(shop)
    
#     # Shopify ISO Format
#     min_date = start_date.strftime("%Y-%m-%dT00:00:00Z")
#     max_date = end_date.strftime("%Y-%m-%dT23:59:59Z")

#     # status=any is critical to see all orders (not just open ones)
#     url = f"{get_base_url(ctx['shop'])}/orders.json?status=any&created_at_min={min_date}&created_at_max={max_date}"
    
#     print(f"🔗 FETCHING ORDERS: {url}")
#     data = safe_get(url, get_headers(ctx["token"]))

#     return data.get("orders", [])


# def get_sales_by_product(shop: str, start_date: date, end_date: date):
#     orders = get_orders(shop, start_date, end_date)

#     sales = {}

#     for order in orders:
#         for item in order.get("line_items", []):
#             pid = str(item["product_id"])

#             if pid not in sales:
#                 sales[pid] = {
#                     "product_id": pid,
#                     "title": item.get("title"),
#                     "units_sold": 0,
#                     "revenue": 0
#                 }

#             sales[pid]["units_sold"] += item["quantity"]
#             sales[pid]["revenue"] += float(item["price"]) * item["quantity"]

#     return sales


# def get_intelligence_summary(shop: str):
#     # For now, let's just get the last 30 days of data
#     from datetime import date, timedelta
#     end_date = date.today()
#     start_date = end_date - timedelta(days=30)
    
#     orders = get_orders(shop, start_date, end_date)
    
#     total_orders = len(orders)
#     net_revenue = sum(float(o.get("total_price", 0)) for o in orders)
#     aov = net_revenue / total_orders if total_orders > 0 else 0
    
#     # We can fake conversion rate for now or calculate if we had traffic data
#     conversion_rate = 0 # Static for now
    
#     return {
#         "net_revenue": net_revenue,
#         "total_orders": total_orders,
#         "avg_order_value": aov,
#         "conversion_rate": conversion_rate,
#         "revenue_change": "+12%", # Placeholder
#         "orders_change": "+5%", # Placeholder
#         "aov_change": "+2%" # Placeholder
#     }


import requests
import logging
from datetime import date, timedelta
from services.shop_context import get_shop_data

logger = logging.getLogger(__name__)


def get_headers(token):
    return {"X-Shopify-Access-Token": token}


def get_base_url(shop):
    return f"https://{shop}/admin/api/2024-01"


def safe_get(url, headers):
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Shopify API Error: {str(e)}")
        return {}


# -----------------------------
# PRODUCTS
# -----------------------------
def get_all_products(shop: str):
    ctx = get_shop_data(shop)

    url = f"{get_base_url(ctx['shop'])}/products.json"
    data = safe_get(url, get_headers(ctx["token"]))

    return data.get("products", [])


# -----------------------------
# ORDERS
# -----------------------------
def get_orders(shop: str, start_date: date, end_date: date):
    ctx = get_shop_data(shop)
    
    min_date = start_date.strftime("%Y-%m-%dT00:00:00Z")
    max_date = end_date.strftime("%Y-%m-%dT23:59:59Z")

    url = f"{get_base_url(ctx['shop'])}/orders.json?status=any&created_at_min={min_date}&created_at_max={max_date}"
    
    logger.info(f"Fetching orders: {url}")
    data = safe_get(url, get_headers(ctx["token"]))

    return data.get("orders", [])


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
                    "net_sales": 0
                }

            price = float(item.get("price", 0))
            qty = item.get("quantity", 0)

            # Gross
            gross = price * qty

            # Discounts
            discount = sum(
                float(d.get("amount", 0))
                for d in item.get("discount_allocations", [])
            )

            net = gross - discount

            sales[pid]["units_sold"] += qty
            sales[pid]["gross_sales"] += gross
            sales[pid]["net_sales"] += net

    return sales


# -----------------------------
# INTELLIGENCE SUMMARY
# -----------------------------
def get_intelligence_summary(shop: str):
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    orders = get_orders(shop, start_date, end_date)
    
    total_orders = len(orders)

    gross_sales = 0
    net_revenue = 0

    for order in orders:
        net_revenue += float(order.get("total_price", 0))

        for item in order.get("line_items", []):
            price = float(item.get("price", 0))
            qty = item.get("quantity", 0)

            gross_sales += price * qty

    avg_order_value = gross_sales / total_orders if total_orders > 0 else 0

    return {
        "gross_sales": round(gross_sales, 2),
        "net_revenue": round(net_revenue, 2),
        "total_orders": total_orders,
        "avg_order_value": round(avg_order_value, 2),
        "conversion_rate": 0,  # placeholder
        "revenue_change": "+12%",  # placeholder
        "orders_change": "+5%",    # placeholder
        "aov_change": "+2%"        # placeholder
    }


# -----------------------------
# TOP PERFORMING PRODUCTS
# -----------------------------
def get_top_performing_products(shop: str, limit: int = 5):
    """
    Fetches top products by revenue in the last 30 days, 
    including their image URLs for the dashboard.
    """
    from datetime import date, timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    # 1. Get all products (to get images and titles)
    all_products = get_all_products(shop)
    product_map = {str(p["id"]): p for p in all_products}
    
    # 2. Get sales by product
    sales_data = get_sales_by_product(shop, start_date, end_date)
    
    # 3. Merge and Sort
    merged = []
    for pid, metrics in sales_data.items():
        base_product = product_map.get(pid, {})
        
        # Get image URL safely
        image_url = None
        if base_product.get("image"):
            image_url = base_product["image"].get("src")
        elif base_product.get("images") and len(base_product["images"]) > 0:
            image_url = base_product["images"][0].get("src")

        merged.append({
            "id": pid,
            "title": metrics["title"],
            "image": image_url,
            "units_sold": metrics["units_sold"],
            "revenue": round(metrics["net_sales"], 2),
            "sku": base_product.get("variants", [{}])[0].get("sku", "N/A")
        })

    # Sort by revenue (descending)
    merged.sort(key=lambda x: x["revenue"], reverse=True)
    
    return merged[:limit]
