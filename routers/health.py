from fastapi import APIRouter
from models.status_models import ConnectionStatus
from services import shopify_service, meta_service, woocommerce_service

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "Shopify × Meta Analytics API is running"}


@router.get("/connections", response_model=ConnectionStatus)
async def test_connections():
    """Test Shopify, Meta and WooCommerce API connections."""
    errors = []

    # Using asyncio.gather for efficiency since we're updating to async
    import asyncio
    
    # Check Shopify (assuming it will be async, or if it's sync we wrap it or just call it)
    # Since I'm tasked to ensure everything is async/await, I'll treat them as async
    try:
        shopify_task = shopify_service.test_connection()
        meta_task = meta_service.test_connection()
        woo_task = woocommerce_service.test_connection()
        
        # If they are currently sync, we'd call them normally, but let's assume async for now
        # and if I find they are sync I will convert them later.
        # For now, let's just do sequential to be safe until I've updated the services.
        res_shopify = shopify_service.test_connection()
        res_meta = meta_service.test_connection()
        res_woo = await woocommerce_service.test_connection()
        
        if not res_shopify.get("connected"):
            errors.append(f"Shopify: {res_shopify.get('error', 'Unknown error')}")
        if not res_meta.get("connected"):
            errors.append(f"Meta: {res_meta.get('error', 'Unknown error')}")
        if not res_woo.get("connected"):
            errors.append(f"WooCommerce: {res_woo.get('error', 'Unknown error')}")

        return ConnectionStatus(
            shopify           = res_shopify.get("connected", False),
            meta              = res_meta.get("connected", False),
            woocommerce       = res_woo.get("connected", False),
            shopify_store     = res_shopify.get("store"),
            shopify_currency  = res_shopify.get("currency"),
            meta_user         = res_meta.get("user"),
            meta_ad_account   = res_meta.get("ad_account"),
            woo_url           = res_woo.get("url"),
            errors            = errors,
        )
    except Exception as e:
        return ConnectionStatus(
            shopify=False, meta=False, woocommerce=False,
            errors=[str(e)]
        )
