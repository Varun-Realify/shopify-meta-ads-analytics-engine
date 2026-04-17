from fastapi import APIRouter
from models.status_models import ConnectionStatus
from services import shopify_service, meta_service

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "Shopify × Meta Analytics API is running"}


# @router.get("/connections", response_model=ConnectionStatus)
# def test_connections():
#     """Test both Shopify and Meta API connections."""
#     errors = []
# 
#     shopify = shopify_service.test_connection()
#     meta    = meta_service.test_connection()
# 
#     if not shopify.get("connected"):
#         errors.append(f"Shopify: {shopify.get('error', 'Unknown error')}")
#     if not meta.get("connected"):
#         errors.append(f"Meta: {meta.get('error', 'Unknown error')}")
# 
#     return ConnectionStatus(
#         shopify           = shopify.get("connected", False),
#         meta              = meta.get("connected", False),
#         shopify_store     = shopify.get("store"),
#         shopify_currency  = shopify.get("currency"),
#         meta_user         = meta.get("user"),
#         meta_ad_account   = meta.get("ad_account"),
#         errors            = errors,
#     )
