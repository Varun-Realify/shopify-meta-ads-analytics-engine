from fastapi import APIRouter, HTTPException, Body
from services.stripe_service import stripe_service
from typing import Dict, Any

router = APIRouter(prefix="/stripe", tags=["Stripe"])

@router.post("/checkout")
async def create_checkout(
    product_name: str = Body(..., embed=True, description="Name of the product"),
    amount: int = Body(..., embed=True, description="Amount in cents/paise (e.g. 2000 for 20.00)"),
    currency: str = Body("inr", embed=True),
    success_url: str = Body("http://localhost:8000/success", embed=True),
    cancel_url: str = Body("http://localhost:8000/cancel", embed=True)
):
    try:
        return await stripe_service.create_checkout_session(
            product_name=product_name,
            amount=amount,
            currency=currency,
            success_url=success_url,
            cancel_url=cancel_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}")
async def get_status(session_id: str):
    try:
        return await stripe_service.get_session_status(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def check_stripe_status():
    """Check if Stripe is configured correctly"""
    return {
        "configured": bool(stripe_service.secret),
        "status": "active" if stripe_service.secret else "missing_keys"
    }
