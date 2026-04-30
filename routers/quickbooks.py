import os
from fastapi import APIRouter, HTTPException, Request
from services.quickbooks_service import quickbooks_service

router = APIRouter(prefix="/quickbooks", tags=["QuickBooks"])

# TEMP in-memory storage (replace with DB later)
qb_tokens = {
    "access_token": None,
    "refresh_token": None,
    "realm_id": None
}


@router.get("/auth")
def get_auth():
    return {"url": quickbooks_service.get_auth_url()}


@router.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    realm_id = request.query_params.get("realmId")

    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    token_data = await quickbooks_service.exchange_code(code)

    qb_tokens["access_token"] = token_data.get("access_token")
    qb_tokens["refresh_token"] = token_data.get("refresh_token")
    qb_tokens["realm_id"] = realm_id

    return {
        "message": "QuickBooks connected successfully",
        "realm_id": realm_id
    }


async def ensure_token():
    # ✅ Check .env first, then memory
    access_token = os.getenv("QB_ACCESS_TOKEN") or qb_tokens["access_token"]
    refresh_token = os.getenv("QB_REFRESH_TOKEN") or qb_tokens["refresh_token"]

    if not access_token:
        raise HTTPException(status_code=400, detail="QuickBooks not connected")

    return access_token


@router.get("/profit-loss")
async def profit_loss(start_date: str = None, end_date: str = None):
    # ✅ Read directly from .env for immediate testing
    access_token = os.getenv("QB_ACCESS_TOKEN")
    realm_id = os.getenv("QB_REALM_ID")

    if not access_token or not realm_id:
        # Fallback to in-memory tokens if not in .env
        access_token = await ensure_token()
        realm_id = qb_tokens["realm_id"]

    if not realm_id:
        raise HTTPException(status_code=400, detail="QuickBooks Realm ID missing")

    try:
        data = await quickbooks_service.get_profit_loss(
            access_token=access_token,
            realm_id=realm_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))