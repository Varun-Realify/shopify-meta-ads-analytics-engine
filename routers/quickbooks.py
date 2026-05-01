import os
from fastapi import APIRouter, HTTPException, Request
from services.quickbooks_service import quickbooks_service
from dotenv import load_dotenv, set_key

load_dotenv()

router = APIRouter(prefix="/quickbooks", tags=["QuickBooks"])

# ✅ Load from .env on startup
qb_tokens = {
    "access_token": os.getenv("QB_ACCESS_TOKEN"),
    "refresh_token": os.getenv("QB_REFRESH_TOKEN"),
    "realm_id": os.getenv("QB_REAL_ID") or os.getenv("QB_REALM_ID")
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

    # In a multi-tenant app, you'd save this to a database linked to the user/session
    # For now, we update memory and .env for the active user
    qb_tokens["access_token"] = token_data.get("access_token")
    qb_tokens["refresh_token"] = token_data.get("refresh_token")
    qb_tokens["realm_id"] = realm_id

    save_tokens_to_env(
        qb_tokens["access_token"],
        qb_tokens["refresh_token"],
        realm_id
    )

    # Redirect back to the frontend dashboard
    from fastapi.responses import RedirectResponse
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(url=f"{frontend_url}?qb_connected=true")


def save_tokens_to_env(access_token, refresh_token, realm_id=None):
    """Save tokens back to .env file so they persist after restart"""
    env_path = ".env"
    set_key(env_path, "QB_ACCESS_TOKEN", access_token)
    set_key(env_path, "QB_REFRESH_TOKEN", refresh_token)
    if realm_id:
        # Check which key is used in .env
        set_key(env_path, "QB_REALM_ID", realm_id)


async def ensure_token():
    """Check if we have tokens, attempt refresh if necessary"""
    if not qb_tokens["access_token"]:
        raise HTTPException(status_code=400, detail="QuickBooks not connected")

    # In a simple implementation, we can try to use the token. 
    # If the API returns 401, then we refresh.
    # However, many implementations refresh every time or check expiry.
    # For this flow, we'll return the current token and let the endpoint handle the refresh logic on failure.
    return qb_tokens["access_token"]


@router.get("/profit-loss")
async def profit_loss(start_date: str = None, end_date: str = None):
    access_token = await ensure_token()

    try:
        # Try with current token
        data = await quickbooks_service.get_profit_loss(
            access_token,
            qb_tokens["realm_id"],
            start_date=start_date,
            end_date=end_date
        )
        return {"status": "success", "data": data}
    except Exception as e:
        # If it fails (likely 401), try to refresh
        if qb_tokens["refresh_token"]:
            try:
                print("Token expired. Attempting auto-refresh...")
                refreshed = await quickbooks_service.refresh_token(
                    qb_tokens["refresh_token"]
                )

                new_access_token = refreshed.get("access_token")
                new_refresh_token = refreshed.get("refresh_token")

                # ✅ Update memory
                qb_tokens["access_token"] = new_access_token
                qb_tokens["refresh_token"] = new_refresh_token

                # ✅ Save to .env so it persists
                save_tokens_to_env(new_access_token, new_refresh_token)

                # ✅ Retry once with the new token
                data = await quickbooks_service.get_profit_loss(
                    new_access_token,
                    qb_tokens["realm_id"],
                    start_date=start_date,
                    end_date=end_date
                )
                return {
                    "status": "success", 
                    "data": data,
                    "refreshed": True
                }
            except Exception as refresh_err:
                raise HTTPException(status_code=401, detail=f"Session expired: {str(refresh_err)}")
        
        raise HTTPException(status_code=400, detail=str(e))
