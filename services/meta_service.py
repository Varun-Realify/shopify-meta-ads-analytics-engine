import httpx
import logging
import asyncio
import time
from datetime import date
from core.config import Config
import os

logger  = logging.getLogger(__name__)
BASE    = "https://graph.facebook.com/v18.0"

async def safe_get(url, params=None, retries=3) -> dict:
    TOKEN   = Config.META_ACCESS_TOKEN
    AD_ACC  = Config.META_AD_ACCOUNT_ID
    
    if params is None:
        params = {}
    params["access_token"] = TOKEN or ""

    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                r    = await client.get(url, params=params, timeout=15.0)
                data = r.json()
                if "error" in data:
                    err = data["error"]
                    raise Exception(f"Meta API Error {err.get('code')}: {err.get('message')}")
                return data
            except Exception as e:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    return {}


async def test_connection() -> dict:
    AD_ACC  = Config.META_AD_ACCOUNT_ID
    try:
        data = await safe_get(f"{BASE}/me", params={"fields": "id,name"})
        return {
            "connected":  True,
            "user":       data.get("name", ""),
            "user_id":    data.get("id", ""),
            "ad_account": AD_ACC,
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def get_all_campaigns() -> list:
    AD_ACC  = Config.META_AD_ACCOUNT_ID
    logger.info("Fetching Meta campaigns...")
    data      = await safe_get(
        f"{BASE}/{AD_ACC}/campaigns",
        params={"fields": "id,name,status,objective,start_time,stop_time,daily_budget,lifetime_budget"}
    )
    campaigns = data.get("data", [])
    result    = []

    for c in campaigns:
        daily    = int(c.get("daily_budget", 0)) / 100
        lifetime = int(c.get("lifetime_budget", 0)) / 100
        result.append({
            "id":              c["id"],
            "name":            c["name"],
            "status":          c.get("status", "UNKNOWN"),
            "objective":       c.get("objective", "Meta"),
            "start_time":      c.get("start_time", "")[:10] if c.get("start_time") else "",
            "stop_time":       c.get("stop_time", "")[:10]  if c.get("stop_time")  else "",
            "daily_budget":    daily,
            "lifetime_budget": lifetime,
            "total_budget":    lifetime if lifetime > 0 else daily,
        })

    logger.info(f"Found {len(result)} campaigns")
    return result


async def get_campaign_insights(campaign_id: str, start_date: date, end_date: date) -> dict:
    try:
        data = await safe_get(
            f"{BASE}/{campaign_id}/insights",
            params={
                "fields":     "spend,impressions,clicks,actions,action_values,ctr,cpm,reach",
                "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
            }
        )
        insights = data.get("data", [{}])
        if not insights:
            return {}

        ins         = insights[0]
        conversions = 0
        revenue     = 0.0

        for action in ins.get("actions", []):
            if action.get("action_type") == "purchase":
                conversions = int(float(action.get("value", 0)))
        for av in ins.get("action_values", []):
            if av.get("action_type") == "purchase":
                revenue = float(av.get("value", 0))

        return {
            "spend":            float(ins.get("spend", 0)),
            "impressions":      int(ins.get("impressions", 0)),
            "clicks":           int(ins.get("clicks", 0)),
            "conversions":      conversions,
            "revenue":          revenue,
            "ctr":              float(ins.get("ctr", 0)),
            "cpm":              float(ins.get("cpm", 0)),
            "reach":            int(ins.get("reach", 0)),
        }
    except Exception as e:
        logger.error(f"Meta Insights error: {str(e)}")
        return {}


async def create_catalog_product(name: str, description: str, link: str, image_url: str, price: float, brand: str):
    """
    EXPERIMENTAL: Add a product to your Meta Catalog via API.
    Requires 'catalog_id' and 'ads_management' permissions.
    """
    CATALOG_ID = os.getenv("META_CATALOG_ID")
    TOKEN = Config.META_ACCESS_TOKEN
    if not CATALOG_ID:
        return {"error": "META_CATALOG_ID not set in .env"}

    url = f"{BASE}/{CATALOG_ID}/items_batch"
    payload = {
        "item_type": "PRODUCT_ITEM",
        "requests": [
            {
                "method": "UPDATE",
                "data": {
                    "retailer_id": f"shopify_{name.lower().replace(' ', '_')}",
                    "name": name,
                    "description": description,
                    "url": link,
                    "image_url": image_url,
                    "price": int(price * 100),
                    "currency": "INR",
                    "brand": brand,
                    "condition": "new",
                    "availability": "in stock"
                }
            }
        ],
        "access_token": TOKEN
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload)
        return r.json()


async def create_test_campaign(name: str):
    """
    Experimental: Create a draft campaign for verification.
    Requires 'ads_management' permission.
    """
    AD_ACC = Config.META_AD_ACCOUNT_ID
    TOKEN = Config.META_ACCESS_TOKEN
    url = f"{BASE}/{AD_ACC}/campaigns"
    payload = {
        "name": name,
        "objective": "OUTCOME_SALES",
        "status": "PAUSED",
        "special_ad_categories": "[]",
        "access_token": TOKEN
    }
    r = requests.post(url, data=payload)
    return r.json()


def get_meta_conversions_realtime(ad_id: str):
    """
    Checks specific Ad conversion count in real-time.
    """
    TOKEN = Config.META_ACCESS_TOKEN
    url = f"{BASE}/{ad_id}/insights"
    params = {
        "fields": "actions,action_values,spend",
        "date_preset": "today",
        "access_token": TOKEN
    }
    return safe_get(url, params=params)


def get_daily_spend_timeseries(campaign_id: str, start_date: date, end_date: date) -> list:
    try:
        data   = safe_get(
            f"{BASE}/{campaign_id}/insights",
            params={
                "fields":         "spend,impressions,clicks,actions",
                "time_range":     f'{{"since":"{start_date}","until":"{end_date}"}}',
                "time_increment": "1",
            }
        )
        result = []
        for d in data.get("data", []):
            conversions = 0
            for action in d.get("actions", []):
                if action.get("action_type") == "purchase":
                    conversions = int(float(action.get("value", 0)))
            result.append({
                "date":        d.get("date_start", ""),
                "spend":       float(d.get("spend", 0)),
                "impressions": int(d.get("impressions", 0)),
                "clicks":      int(d.get("clicks", 0)),
                "conversions": conversions,
            })
        return result
    except Exception as e:
        logger.warning(f"Could not fetch timeseries for campaign {campaign_id}: {e}")
        return []
