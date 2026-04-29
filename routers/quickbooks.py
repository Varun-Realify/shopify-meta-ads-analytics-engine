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
    if not qb_tokens["access_token"]:
        raise HTTPException(status_code=400, detail="QuickBooks not connected")

    # Try API with current token
    try:
        return qb_tokens["access_token"]
    except:
        # Refresh if needed
        refreshed = await quickbooks_service.refresh_token(qb_tokens["refresh_token"])

        qb_tokens["access_token"] = refreshed.get("access_token")
        qb_tokens["refresh_token"] = refreshed.get("refresh_token")

        return qb_tokens["access_token"]


@router.get("/profit-loss")
async def profit_loss():
    access_token = await ensure_token()

    data = await quickbooks_service.get_profit_loss(
        access_token,
        qb_tokens["realm_id"]
    )

    return {
        "status": "success",
        "data": data
    }