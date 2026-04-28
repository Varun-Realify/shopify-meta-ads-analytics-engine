from fastapi import APIRouter, HTTPException, Query
from services.plaid_service import plaid_service

router = APIRouter(prefix="/plaid", tags=["Plaid"])

# simple in-memory store (demo only)
_access_token_storage = {}


# --------------------------------------------------
# 🔹 INTERNAL: CREATE OR REUSE ACCESS TOKEN
# --------------------------------------------------
async def get_or_create_access_token(user_id: str):
    access_token = _access_token_storage.get(user_id)

    if not access_token:
        print("🆕 Creating Plaid sandbox access token...")

        # Step 1: create public_token (sandbox)
        sandbox = await plaid_service._post("/sandbox/public_token/create", {
            "client_id": plaid_service.client_id,
            "secret": plaid_service.secret,
            "institution_id": "ins_109508",  # Chase sandbox
            "initial_products": ["transactions"]
        })

        public_token = sandbox["public_token"]

        # Step 2: exchange → access_token
        exchange = await plaid_service._post("/item/public_token/exchange", {
            "client_id": plaid_service.client_id,
            "secret": plaid_service.secret,
            "public_token": public_token
        })

        access_token = exchange["access_token"]
        _access_token_storage[user_id] = access_token

    else:
        print("⚡ Using cached Plaid token")

    return access_token


# --------------------------------------------------
# 🔹 TEST CONNECTION
# --------------------------------------------------
@router.get("/test")
async def test_connection():
    try:
        return await plaid_service.test_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# 🔹 GET ACCOUNTS
# --------------------------------------------------
@router.get("/accounts")
async def get_accounts(user_id: str = Query("default")):
    try:
        access_token = await get_or_create_access_token(user_id)
        return await plaid_service.get_accounts(access_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# 🔹 GET TRANSACTIONS
# --------------------------------------------------
@router.get("/transactions")
async def get_transactions(
    start_date: str = Query(...),
    end_date: str = Query(...),
    user_id: str = Query("default")
):
    try:
        access_token = await get_or_create_access_token(user_id)

        result = await plaid_service.get_transactions(access_token, start_date, end_date)
        transactions = result.get("transactions", [])

        # transform for frontend
        transformed = []
        for tx in transactions:
            transformed.append({
                "transaction_id": tx.get("transaction_id"),
                "account_id": tx.get("account_id"),
                "amount": tx.get("amount"),
                "date": tx.get("date"),
                "name": tx.get("name"),
                "merchant_name": tx.get("merchant_name"),
                "category": (
                    tx.get("category", [{}])[0].get("primary")
                    if tx.get("category") else None
                ),
                "pending": tx.get("pending"),
                "payment_channel": tx.get("payment_channel")
            })

        # expenses = positive values
        total_expenses = sum(
            tx["amount"] for tx in transactions if tx.get("amount", 0) > 0
        )

        return {
            "transactions": transformed,
            "total_transactions": len(transformed),
            "total_expenses": round(total_expenses, 2),
            "accounts": result.get("accounts", []),
            "item": result.get("item", {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plaid error: {str(e)}")


# --------------------------------------------------
# 🔹 STATUS
# --------------------------------------------------
@router.get("/status")
async def get_status():
    return {
        "configured": bool(plaid_service.client_id and plaid_service.secret),
        "environment": plaid_service.env,
        "linked": bool(_access_token_storage.get("default"))
    }