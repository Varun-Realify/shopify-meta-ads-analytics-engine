import os
from fastapi import APIRouter, HTTPException, Request, Query
from services.quickbooks_service import quickbooks_service
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/quickbooks", tags=["QuickBooks"])


@router.get("/auth")
def get_auth(user_id: str = Query(..., description="The ID of the user requesting auth")):
    return {"url": quickbooks_service.get_auth_url(user_id)}


@router.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    realm_id = request.query_params.get("realmId")
    state = request.query_params.get("state") # user_id is passed back in state

    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    token_data = await quickbooks_service.exchange_code(code)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    user_id = state or "default"

    await quickbooks_service.save_tokens(
        user_id,
        realm_id,
        access_token,
        refresh_token
    )

    # Redirect back to the frontend dashboard
    from fastapi.responses import RedirectResponse
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(url=f"{frontend_url}?qb_connected=success&user_id={user_id}")


async def ensure_token(user_id: str):
    """Check if we have tokens, attempt refresh if necessary"""
    token_data = await quickbooks_service.get_tokens(user_id)
    if not token_data or not token_data.get("access_token"):
        raise HTTPException(status_code=400, detail="QuickBooks not connected")
    
    return token_data


@router.get("/profit-loss")
async def profit_loss(user_id: str = Query(...), start_date: str = None, end_date: str = None):
    token_data = await ensure_token(user_id)
    
    access_token = token_data.get("access_token")
    realm_id = token_data.get("realm_id")
    refresh_token = token_data.get("refresh_token")

    try:
        # Try with current token
        data = await quickbooks_service.get_profit_loss(
            access_token,
            realm_id,
            start_date=start_date,
            end_date=end_date
        )
        return {"status": "success", "data": data}
    except Exception as e:
        # If it fails (likely 401), try to refresh
        if refresh_token:
            try:
                print(f"Token expired for user {user_id}. Attempting auto-refresh...")
                refreshed = await quickbooks_service.refresh_token(refresh_token)

                new_access_token = refreshed.get("access_token")
                new_refresh_token = refreshed.get("refresh_token")

                # ✅ Save to DB so it persists
                await quickbooks_service.save_tokens(
                    user_id,
                    realm_id,
                    new_access_token,
                    new_refresh_token
                )

                # ✅ Retry once with the new token
                data = await quickbooks_service.get_profit_loss(
                    new_access_token,
                    realm_id,
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
