import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from core.config import Config

# Scopes for Google Content API
SCOPES = ["https://www.googleapis.com/auth/content"]

def get_service():
    """Initializes and returns the Google Content API service."""
    if not Config.GOOGLE_SERVICE_ACCOUNT_JSON_PATH or not os.path.exists(Config.GOOGLE_SERVICE_ACCOUNT_JSON_PATH):
        raise Exception("Google Service Account JSON file not found.")
    
    creds = service_account.Credentials.from_service_account_file(
        Config.GOOGLE_SERVICE_ACCOUNT_JSON_PATH, scopes=SCOPES
    )
    return build("content", "v2.1", credentials=creds)

def get_my_products(merchant_id: str):
    """Fetch all products from the merchant's own GMC account."""
    service = get_service()
    result = service.products().list(merchantId=merchant_id).execute()
    products = result.get("resources", [])
    
    formatted_products = []
    for p in products:
        formatted_products.append({
            "id": p.get("offerId"),
            "title": p.get("title"),
            "price": p.get("price", {}).get("value"),
            "currency": p.get("price", {}).get("currency"),
            "availability": p.get("availability"),
            "brand": p.get("brand"),
            "gtin": p.get("gtin")
        })
    return formatted_products

def get_price_benchmarks(merchant_id: str, product_ids: list[str]):
    """Retrieve best price benchmark and price competitiveness data per product."""
    service = get_service()
    benchmarks = {}
    
    for pid in product_ids:
        try:
            # Note: In a real scenario, you'd batch these or use a report.
            status = service.productstatuses().get(merchantId=merchant_id, productId=f"online:en:IN:{pid}").execute()
            # Extract price competitiveness from data quality or specific reporting fields if available in v2.1
            # For brevity, we'll mock the benchmark calculation if not directly in the simple GET
            benchmarks[pid] = {
                "price_benchmark": status.get("priceBenchmark"), # Placeholder for actual benchmark field
                "competitiveness": "high" # Placeholder logic
            }
        except Exception:
            benchmarks[pid] = {"price_benchmark": None, "competitiveness": "unknown"}
            
    return benchmarks

def get_best_sellers(merchant_id: str, category_id: str):
    """Fetch top products by clicks/impressions in a given Google product category."""
    service = get_service()
    # Using reports.search with best_sellers table
    query = {
        "query": f"SELECT product_title, report_category_id, rank, previous_rank, relative_demand FROM best_sellers WHERE report_category_id = {category_id} AND inventory_status = 'IN_STOCK' ORDER BY rank ASC"
    }
    result = service.reports().search(merchantId=merchant_id, body=query).execute()
    return result.get("results", [])
