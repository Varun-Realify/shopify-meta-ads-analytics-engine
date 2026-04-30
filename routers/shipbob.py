from fastapi import APIRouter, HTTPException
from services.shipbob_service import shipbob_service

router = APIRouter(prefix="/shipbob", tags=["ShipBob Fulfillment"])

@router.get("/test")
async def test_connection():
    result = await shipbob_service.test_connection()
    if not result["connected"]:
        raise HTTPException(status_code=502, detail=result["error"])
    return result

@router.get("/inventory")
async def get_inventory():
    try:
        inventory = await shipbob_service.get_inventory()
        return {"inventory": inventory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders")
async def get_orders():
    try:
        orders = await shipbob_service.get_orders()
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
