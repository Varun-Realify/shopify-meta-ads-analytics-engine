from datetime import date, timedelta
import difflib
from core.config import Config


# ── Pure Metric Functions ─────────────────────────────────────────────────────

def calculate_roas(revenue: float, ad_spend: float) -> float:
    return round(revenue / ad_spend, 2) if ad_spend > 0 else 0.0

def calculate_cpa(ad_spend: float, conversions: int) -> float:
    return round(ad_spend / conversions, 2) if conversions > 0 else 0.0

def calculate_ctr(clicks: int, impressions: int) -> float:
    return round((clicks / impressions) * 100, 2) if impressions > 0 else 0.0

def calculate_profit(revenue: float, units_sold: int, cost_price: float, ad_spend: float) -> float:
    return round(revenue - (cost_price * units_sold) - ad_spend, 2)

def calculate_profit_margin(profit: float, revenue: float) -> float:
    return round((profit / revenue) * 100, 2) if revenue > 0 else 0.0

def calculate_sales_lift(before_avg: float, during_avg: float) -> float:
    return round(((during_avg - before_avg) / before_avg) * 100, 2) if before_avg > 0 else 0.0

def calculate_breakeven_units(ad_spend: float, selling_price: float, cost_price: float) -> float:
    margin = selling_price - cost_price
    return round(ad_spend / margin, 2) if margin > 0 else 0.0

def calculate_true_roas(before_avg_rev: float, during_avg_rev: float,
                        duration_days: int, ad_spend: float) -> float:
    incremental = max(0, during_avg_rev - before_avg_rev) * duration_days
    return round(incremental / ad_spend, 2) if ad_spend > 0 else 0.0

def total_cogs(orders):
    return sum(
        item.get("cost", 0) * item.get("quantity", 0)
        for o in orders
        for item in o.get("items", [])
    )

def calculate_cac(ad_spend, new_customers):
    return round(ad_spend / new_customers, 2) if new_customers else 0

def get_top_products(orders):
    product_stats = {}

    for order in orders:
        for item in order.get("items", []):
            title = item.get("product_title", "Unknown")
            revenue = item.get("price", 0) * item.get("quantity", 0)
            cost = item.get("cost", 0) * item.get("quantity", 0)

            if title not in product_stats:
                product_stats[title] = {
                    "product_title": title,
                    "total_quantity": 0,
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                    "total_profit": 0.0
                }
            
            product_stats[title]["total_quantity"] += item.get("quantity", 0)
            product_stats[title]["total_revenue"] += revenue
            product_stats[title]["total_cost"] += cost
            product_stats[title]["total_profit"] += (revenue - cost)
    
    sorted_products = sorted(
        product_stats.values(),
        key=lambda x: x["total_revenue"],
        reverse=True
    )

    for p in sorted_products:
        p["total_revenue"] = round(p["total_revenue"], 2)
        p["total_cost"] = round(p["total_cost"], 2)
        p["total_profit"] = round(p["total_profit"], 2)

    return sorted_products


# ── Period Classifier ─────────────────────────────────────────────────────────

def get_period_sales(daily_timeseries: list, campaign_start: date,
                     campaign_end: date, window: int = 30) -> dict:
    before, during, after = [], [], []

    for record in daily_timeseries:
        d = date.fromisoformat(record["date"])
        if campaign_start <= d <= campaign_end:
            during.append(record)
        elif (campaign_start - timedelta(days=window)) <= d < campaign_start:
            before.append(record)
        elif campaign_end < d <= (campaign_end + timedelta(days=window)):
            after.append(record)

    def stats(records):
        if not records:
            return {"avg_daily_units": 0.0, "total_revenue": 0.0, "total_units": 0, "days": 0}
        return {
            "avg_daily_units": round(sum(r["units_sold"] for r in records) / len(records), 2),
            "total_revenue":   round(sum(r["revenue"]    for r in records), 2),
            "total_units":     sum(r["units_sold"] for r in records),
            "days":            len(records),
        }

    return {"before": stats(before), "during": stats(during), "after": stats(after)}


# ── Product Matching ──────────────────────────────────────────────────────────

def find_matching_product(campaign_name: str, products_list: list, camp_sales: dict) -> dict:
    best_match_id = None
    best_match_title = None
    highest_ratio = 0.0
    
    # 1. Fuzzy Name Matching
    campaign_name_lower = campaign_name.lower().strip('"\' ')
    for product in products_list:
        title = product.get("title", "").lower()
        if not title: continue
        
        # Check explicit inclusion
        if title in campaign_name_lower or campaign_name_lower in title:
            return {"product_id": product["id"], "title": product["title"], "match_type": "exact_name"}

        ratio = difflib.SequenceMatcher(None, campaign_name_lower, title).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match_id = product["id"]
            best_match_title = product["title"]

    if highest_ratio > 0.4 and best_match_id:
        return {"product_id": best_match_id, "title": best_match_title, "match_type": "name_similarity"}

    # 2. Fallback to Best Seller during the period
    if camp_sales:
        best_selling = sorted(camp_sales.values(), key=lambda x: x["units_sold"], reverse=True)
        if best_selling and best_selling[0]["units_sold"] > 0:
            return {"product_id": best_selling[0]["product_id"], "title": best_selling[0]["title"], "match_type": "top_seller"}

    # 3. Ultimate Fallback
    if products_list:
        return {"product_id": products_list[0]["id"], "title": products_list[0]["title"], "match_type": "random_fallback"}
        
    return {"product_id": "", "title": "Unknown", "match_type": "none"}


# ── Recommendation Engine ─────────────────────────────────────────────────────

def generate_recommendation(metrics: dict) -> dict:
    roas          = metrics.get("roas", 0)
    profit        = metrics.get("profit", 0)
    profit_margin = metrics.get("profit_margin", 0)
    sales_lift    = metrics.get("sales_lift", 0)
    ctr           = metrics.get("ctr", 0)
    cpa           = metrics.get("cpa", 0)
    true_roas     = metrics.get("true_roas", 0)
    ad_spend      = metrics.get("ad_spend", 0)
    selling_price = metrics.get("selling_price", 0)
    cost_price    = metrics.get("cost_price", 0)

    warnings = []

    if ad_spend == 0 and profit == 0:
        level    = " PENDING DATA"
        headline = "No Spend or Revenue tracked yet"
        detail   = "This campaign is active but hasn't spent anything or recorded any sales in the selected period."
        action   = "Wait 24-48 hours for Meta Pixel tracking data to populate."
        priority = 0

    elif roas < 1:
        level    = " STOP"
        headline = "Campaign is LOSING money"
        detail   = (f"Spending $100 returns only ${roas*100:.2f}. "
                    f"Net loss: ${abs(profit):.2f}")
        action   = "Pause immediately. Reallocate budget to profitable campaigns."
        priority = abs(profit)

    elif roas < 2:
        level    = " OPTIMIZE"
        headline = "Marginal returns — needs optimization"
        detail   = f"ROAS {roas:.2f}x barely profitable at {profit_margin:.1f}% margin."
        action   = "Cut budget 30%, A/B test new creatives, refine audience targeting."
        priority = ad_spend * 0.3

    elif roas < 3:
        level    = " SCALE"
        headline = "Good performance — scale carefully"
        detail   = f"ROAS {roas:.2f}x with {profit_margin:.1f}% margin. ${profit:.2f} profit."
        action   = "Increase budget by 20% weekly. Monitor CPA as you scale."
        priority = profit * 0.2

    else:
        level    = " AGGRESSIVE SCALE"
        headline = "Excellent ROI — scale aggressively"
        detail   = f"ROAS {roas:.2f}x. Every $1 returns ${roas:.2f}. {profit_margin:.1f}% margin."
        action   = "Double the budget. Expand to lookalike audiences immediately."
        priority = profit * 0.5

    if sales_lift < 10:
        warnings.append(f" Low lift (+{sales_lift:.1f}%): Review targeting and creatives.")
    if profit_margin < 15:
        warnings.append(f" Thin margins ({profit_margin:.1f}%): Raise price or cut spend.")
    if ctr < 1.0:
        warnings.append(f" Low CTR ({ctr:.2f}%): Test new ad images and copy.")
    gross = selling_price - cost_price
    if cpa > gross > 0:
        warnings.append(f" CPA (${cpa:.2f}) exceeds gross profit per unit (${gross:.2f}).")
    if true_roas > 0 and true_roas < roas * 0.5:
        warnings.append(f" True ROAS is only {true_roas:.2f}x — sales may be mostly organic.")

    return {
        "level":          level,
        "headline":       headline,
        "detail":         detail,
        "action":         action,
        "warnings":       warnings,
        "priority_score": round(priority, 2),
    }
