


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


# -----------------------------
# HELPERS: COST FETCHING
# -----------------------------
def get_inventory_costs(shop: str, inventory_item_ids: list):
    """
    Fetches the cost for a list of inventory item IDs.
    Shopify REST limit for this endpoint is usually 250 IDs per request.
    """
    if not inventory_item_ids:
        return {}
        
    ctx = get_shop_data(shop)
    # Split into chunks of 100 to stay safe
    chunk_size = 100
    costs = {}
    
    for i in range(0, len(inventory_item_ids), chunk_size):
        chunk = inventory_item_ids[i:i + chunk_size]
        ids_str = ",".join(map(str, chunk))
        url = f"{get_base_url(ctx['shop'])}/inventory_items.json?ids={ids_str}"
        data = safe_get(url, get_headers(ctx["token"]))
        
        for item in data.get("inventory_items", []):
            costs[str(item["id"])] = float(item.get("cost") or 0)
            
    return costs


# -----------------------------
# MARGIN INTELLIGENCE
# -----------------------------
def get_margin_intelligence(shop: str):
    """
    Calculates COGS, Gross Profit, and Net Profit for the last 30 days.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    orders = get_orders(shop, start_date, end_date)
    
    items_sold = []
    inventory_item_ids = set()
    total_revenue = 0
    
    for o in orders:
        total_revenue += float(o.get("total_price", 0))
        for li in o.get("line_items", []):
            iid = li.get("product_id") # We actually need variant info for cost
            # Line items in REST have 'variant_id' but not 'inventory_item_id'
            # We need to map variants to retrieve costs
            items_sold.append({
                "variant_id": li.get("variant_id"),
                "qty": li.get("quantity", 0),
                "price": float(li.get("price", 0)),
                "title": li.get("title")
            })

    # To get costs, we need inventory_item_ids for these variants
    # Fetch all products to get the mapping
    all_products = get_all_products(shop)
    variant_to_cost_id = {}
    for p in all_products:
        for v in p.get("variants", []):
            variant_to_cost_id[v["id"]] = v["inventory_item_id"]

    # Unique inventory item IDs needed
    cost_ids = list(set(variant_to_cost_id.values()))
    costs_map = get_inventory_costs(shop, cost_ids)
    
    total_cogs = 0
    product_margins = {}

    for item in items_sold:
        vid = item["variant_id"]
        cost_id = variant_to_cost_id.get(vid)
        cost = costs_map.get(str(cost_id), 0)
        
        item_cogs = cost * item["qty"]
        total_cogs += item_cogs
        
        # Track per-product margin for watchlist
        title = item["title"]
        if title not in product_margins:
            product_margins[title] = {"revenue": 0, "cogs": 0, "qty": 0}
        
        product_margins[title]["revenue"] += item["price"] * item["qty"]
        product_margins[title]["cogs"] += item_cogs
        product_margins[title]["qty"] += item["qty"]

    gross_profit = total_revenue - total_cogs
    gross_margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Format watchlist
    watchlist = []
    for title, m in product_margins.items():
        margin_pct = ((m["revenue"] - m["cogs"]) / m["revenue"] * 100) if m["revenue"] > 0 else 0
        watchlist.append({
            "title": title,
            "revenue": round(m["revenue"], 2),
            "margin_pct": round(margin_pct, 1),
            "is_low": margin_pct < 20
        })
        
    watchlist.sort(key=lambda x: x["margin_pct"])

    return {
        "net_revenue": round(total_revenue, 2),
        "total_cogs": round(total_cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": round(gross_margin_pct, 1),
        "operating_expenses": 0, # Placeholder
        "net_profit": round(gross_profit, 2), # Placeholder (GP - OpExp)
        "watchlist": watchlist[:5]
    }


# -----------------------------
# INVENTORY INTELLIGENCE
# -----------------------------
def get_inventory_intelligence(shop: str):
    """
    Calculates Total Inventory Value, Stock Accuracy, and Turnover.
    """
    all_products = get_all_products(shop)
    
    inventory_item_ids = []
    variant_data = []
    
    for p in all_products:
        image_url = None
        if p.get("image"):
            image_url = p["image"].get("src")
            
        for v in p.get("variants", []):
            inventory_item_ids.append(v["inventory_item_id"])
            variant_data.append({
                "title": p["title"],
                "variant_title": v["title"],
                "inventory_item_id": v["inventory_item_id"],
                "sku": v.get("sku"),
                "stock": v.get("inventory_quantity", 0),
                "image": image_url
            })
            
    costs_map = get_inventory_costs(shop, inventory_item_ids)
    
    total_value = 0
    watchlist = []
    
    for v in variant_data:
        cost = costs_map.get(str(v["inventory_item_id"]), 0)
        item_value = cost * v["stock"]
        total_value += item_value
        
        watchlist.append({
            "title": v["title"],
            "sku": v["sku"],
            "stock": v["stock"],
            "value": round(item_value, 2),
            "image": v["image"],
            "is_low": v["stock"] < 10
        })

    watchlist.sort(key=lambda x: x["stock"])

    return {
        "total_inventory_value": round(total_value, 2),
        "inventory_turnover": 0.8, # Placeholder
        "days_of_inventory": 45,   # Placeholder
        "stock_accuracy": 98.5,    # Placeholder
        "total_items": len(variant_data),
        "watchlist": watchlist[:5]
    }
