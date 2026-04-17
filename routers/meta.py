from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from services import shopify_service, meta_service

router = APIRouter(prefix="/meta", tags=["Meta"])

@router.post("/catalog/sync")
def sync_shopify_to_meta():
    """Sync all Shopify products to Meta Catalog."""
    try:
        products = shopify_service.get_all_products()
        results = []
        for p in products:
            res = meta_service.create_catalog_product(
                name=p["title"],
                description=f"Shopify product {p['title']}",
                link=f"https://{shopify_service.Config.SHOPIFY_STORE_NAME}/products/{p['id']}",
                image_url="", # Would normally fetch from Shopify image API
                price=p["selling_price"],
                brand=p.get("vendor", "Generic")
            )
            results.append({"product": p["title"], "status": res})
        return {"total_synced": len(results), "details": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns")
def get_campaigns():
    """Fetch all Meta ad campaigns."""
    try:
        campaigns = meta_service.get_all_campaigns()
        return {"count": len(campaigns), "campaigns": campaigns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}/insights")
def get_campaign_insights(
    campaign_id: str,
    start_date:  date = date.today() - timedelta(days=30),
    end_date:    date = date.today()
):
    """Get performance insights for a specific campaign."""
    try:
        insights = meta_service.get_campaign_insights(campaign_id, start_date, end_date)
        return {"campaign_id": campaign_id, "period": f"{start_date} → {end_date}", **insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}/timeseries")
def get_campaign_timeseries(
    campaign_id: str,
    start_date:  date = date.today() - timedelta(days=30),
    end_date:    date = date.today()
):
    """Get daily spend/performance breakdown for a campaign."""
    try:
        ts = meta_service.get_daily_spend_timeseries(campaign_id, start_date, end_date)
        return {"campaign_id": campaign_id, "days": len(ts), "timeseries": ts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
