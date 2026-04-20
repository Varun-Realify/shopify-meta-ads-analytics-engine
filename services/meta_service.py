import httpx
import logging
import asyncio
from datetime import date
from core.config import Config

logger  = logging.getLogger(__name__)
BASE    = "https://graph.facebook.com/v18.0"
TOKEN   = Config.META_ACCESS_TOKEN
AD_ACC  = Config.META_AD_ACCOUNT_ID


async def safe_get(client: httpx.AsyncClient, url: str, params=None, retries=3) -> dict:
    if params is None:
        params = {}
    params["access_token"] = TOKEN or ""

    for attempt in range(retries):
        try:
            r    = await client.get(url, params=params, timeout=15)
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
    try:
        async with httpx.AsyncClient() as client:
            data = await safe_get(client, f"{BASE}/me", params={"fields": "id,name"})
            return {
                "connected":  True,
                "user":       data.get("name", ""),
                "user_id":    data.get("id", ""),
                "ad_account": AD_ACC,
            }
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def get_all_campaigns() -> list:
    logger.info("Fetching Meta campaigns...")
    async with httpx.AsyncClient() as client:
        data      = await safe_get(
            client,
            f"{BASE}/{AD_ACC}/campaigns",
            params={"fields": "id,name,status,start_time,stop_time,daily_budget,lifetime_budget"}
        )
        campaigns = data.get("data", [])
        for c in campaigns:
            c["total_budget"] = float(c.get("daily_budget", 0) or c.get("lifetime_budget", 0)) / 100
        return campaigns


async def get_campaign_insights(campaign_id: str, start_date: date, end_date: date) -> dict:
    async with httpx.AsyncClient() as client:
        data = await safe_get(
            client,
            f"{BASE}/{campaign_id}/insights",
            params={
                "time_range": f"{{\"since\":\"{start_date}\",\"until\":\"{end_date}\"}}",
                "fields":     "spend,impressions,clicks,conversions,purchase_revenue,actions",
            }
        )
        insights = data.get("data", [{}])[0] if data.get("data") else {}
        
        conversions = 0
        if "actions" in insights:
            for action in insights["actions"]:
                if action["action_type"] in ["offsite_conversion.fb_pixel_purchase", "purchase"]:
                    conversions = int(action["value"])
                    break

        return {
            "spend":            float(insights.get("spend", 0)),
            "impressions":      int(insights.get("impressions", 0)),
            "clicks":           int(insights.get("clicks", 0)),
            "conversions":      conversions,
            "purchase_revenue": float(insights.get("purchase_revenue", 0)),
        }


async def get_daily_spend_timeseries(campaign_id: str, start_date: date, end_date: date) -> list:
    async with httpx.AsyncClient() as client:
        data = await safe_get(
            client,
            f"{BASE}/{campaign_id}/insights",
            params={
                "time_range": f"{{\"since\":\"{start_date}\",\"until\":\"{end_date}\"}}",
                "fields":     "spend,date_start",
                "time_increment": 1,
            }
        )
        return [{"date": i["date_start"], "spend": float(i["spend"])} for i in data.get("data", [])]


async def create_catalog_product(name, description, link, image_url, price, brand):
    return "success"
