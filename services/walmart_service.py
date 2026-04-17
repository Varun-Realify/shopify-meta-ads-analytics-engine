import httpx
import logging
import asyncio
import base64
import uuid
from datetime import date
from core.config import Config

logger = logging.getLogger(__name__)

# Walmart API Constants
WALMART_AUTH_URL = "https://marketplace.walmartapis.com/v3/token"
WALMART_BASE_URL = "https://marketplace.walmartapis.com/v3"

async def get_walmart_token():
    """Retrieves an OAuth2 token from Walmart Marketplace."""
    if not Config.WALMART_CLIENT_ID or not Config.WALMART_CLIENT_SECRET:
        logger.error("Walmart credentials not configured")
        return None

    # Correlation ID is required by Walmart
    correlation_id = str(uuid.uuid4())
    
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{Config.WALMART_CLIENT_ID}:{Config.WALMART_CLIENT_SECRET}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded",
        "WM_SVC.NAME": "Walmart Marketplace",
        "WM_QOS.CORRELATION_ID": correlation_id,
        "Accept": "application/json"
    }
    
    data = {
        "grant_type": "client_credentials"
    }

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(WALMART_AUTH_URL, headers=headers, data=data, timeout=15)
            r.raise_for_status()
            token_data = r.json()
            return token_data.get("access_token")
        except Exception as e:
            logger.error(f"Failed to get Walmart token: {e}")
            return None

async def walmart_request(method, endpoint, params=None, json_data=None, retries=3):
    """Generic Walmart API request helper with OAuth2 and correlation handling."""
    token = await get_walmart_token()
    if not token:
        raise Exception("Walmart: Failed to obtain access token")

    url = f"{WALMART_BASE_URL}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "WM_SEC.ACCESS_TOKEN": token,
        "WM_SVC.NAME": "Walmart Marketplace",
        "WM_QOS.CORRELATION_ID": str(uuid.uuid4()),
        "Accept": "application/json"
    }
    
    if Config.WALMART_CHANNEL_TYPE:
        headers["WM_CONSUMER.CHANNEL.TYPE"] = Config.WALMART_CHANNEL_TYPE

    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                r = await client.request(method, url, headers=headers, params=params, json=json_data, timeout=30)
                
                if r.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                    
                r.raise_for_status()
                return r.json()
            except httpx.RequestError as e:
                if attempt == retries - 1:
                    raise Exception(f"Walmart API error: {e}")
                await asyncio.sleep(2 ** attempt)
        return {}

async def test_connection() -> dict:
    """Verifies connection by fetching some basic item data or similar."""
    try:
        # Using a simple GET products call with limit 1 as a health check
        data = await walmart_request("GET", "items", params={"limit": 1})
        return {
            "connected": True,
            "client_id": Config.WALMART_CLIENT_ID,
            "message": "Successfully connected to Walmart Marketplace API"
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}

async def get_all_products() -> list:
    """Fetches items from Walmart Marketplace and maps them to ProductModel."""
    logger.info("Fetching Walmart products...")
    try:
        # Walmart Item API: GET /v3/items
        data = await walmart_request("GET", "items", params={"limit": 100})
        items = data.get("ItemResponse", [])
        result = []

        for item in items:
            sku = item.get("sku", "")
            product_name = item.get("productName", "Unknown")
            price = float(item.get("price", {}).get("amount", 0.0))
            
            result.append({
                "id": sku,
                "title": product_name,
                "vendor": "Walmart",
                "product_type": "Marketplace Item",
                "selling_price": price,
                "cost_price": 0.0,
                "stock": item.get("lifecycleStatus", "") == "ACTIVE"
            })

        logger.info(f"Found {len(result)} Walmart products")
        return result
    except Exception as e:
        logger.error(f"Error fetching Walmart products: {e}")
        return []

async def get_orders(start_date: date, end_date: date) -> list:
    """Fetches orders from Walmart Marketplace."""
    logger.info(f"Fetching Walmart orders {start_date} → {end_date}...")
    try:
        params = {
            "createdStartDate": f"{start_date}T00:00:00Z",
            "createdEndDate": f"{end_date}T23:59:59Z",
            "limit": 100
        }
        data = await walmart_request("GET", "orders", params=params)
        return data.get("list", {}).get("elements", {}).get("order", [])
    except Exception as e:
        logger.error(f"Error fetching Walmart orders: {e}")
        return []
