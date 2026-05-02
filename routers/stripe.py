from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from typing import Optional
from services.stripe_service import stripe_service
from models.stripe_models import StripeHistoryResponse  # Import your model

router = APIRouter(prefix="/stripe", tags=["Stripe"])

@router.get("/callback")
async def stripe_callback(code: str, state: str):
    try:
        result = await stripe_service.exchange_token_and_save(code, state)
        
        # Change this to your actual frontend URL
        FRONTEND_DASHBOARD_URL = "http://localhost:5173"
        
        # Redirect the user back to the frontend, passing a success flag and the user ID
        return RedirectResponse(url=f"{FRONTEND_DASHBOARD_URL}?stripe_connected=success&user_id={state}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Detailed Error: {str(e)} | Type: {type(e).__name__}")

@router.get("/history/{user_id}", response_model=StripeHistoryResponse)
async def get_payment_history(user_id: str):
    """Fetches the gathered financial data using the stored MongoDB token."""
    try:
        history = await stripe_service.get_seller_payment_data(user_id)
        return {
            "user_id": user_id,
            "total_transactions": len(history),
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))