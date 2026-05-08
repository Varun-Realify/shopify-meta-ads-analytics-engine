from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from services.plaid_service import plaid_service
from models.plaid_models import (
    LinkTokenRequest,
    LinkTokenResponse,
    ExchangeTokenRequest,
    ExchangeTokenResponse,
    UserConnectionsResponse,
    PlaidConnectionInfo,
    PlaidStatusResponse,
)

router = APIRouter(prefix="/plaid", tags=["Plaid"])


@router.post("/link_token", response_model=LinkTokenResponse)
async def create_link_token(body: LinkTokenRequest):
    try:
        result = await plaid_service.create_link_token(body.user_id)
        return LinkTokenResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exchange_token", response_model=ExchangeTokenResponse)
async def exchange_token(body: ExchangeTokenRequest):
    try:
        result = await plaid_service.exchange_and_store(
            user_id=body.user_id,
            public_token=body.public_token,
        )

        return ExchangeTokenResponse(**result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts")
async def get_accounts(
    user_id: str = Query(...),
    item_id: Optional[str] = Query(None),
):
    try:
        return await plaid_service.get_accounts_for_user(
            user_id=user_id,
            item_id=item_id,
        )

    except Exception as e:
        detail = str(e)
        status_code = 404 if "No Plaid connection" in detail else 500
        raise HTTPException(status_code=status_code, detail=detail)


@router.get("/transactions")
async def get_transactions(
    user_id: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    item_id: Optional[str] = Query(None),
    count: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    try:
        result = await plaid_service.get_transactions_for_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            item_id=item_id,
            count=count,
            offset=offset,
        )

        transactions = result.get("transactions", [])

        transformed = []

        for tx in transactions:
            category = (
                tx.get("personal_finance_category", {}).get("primary")
                or (tx.get("category") or [None])[0]
            )

            transformed.append({
                "transaction_id": tx.get("transaction_id"),
                "account_id": tx.get("account_id"),
                "amount": tx.get("amount"),
                "date": tx.get("date"),
                "name": tx.get("name"),
                "merchant_name": tx.get("merchant_name"),
                "category": category,
                "pending": tx.get("pending"),
                "payment_channel": tx.get("payment_channel"),
            })

        total_expenses = round(
            sum(
                tx["amount"]
                for tx in transactions
                if tx.get("amount", 0) > 0
            ),
            2,
        )

        return {
            "user_id": user_id,
            "item_id": result.get("item_id"),
            "institution_name": result.get("institution_name"),
            "transactions": transformed,
            "total_transactions": len(transformed),
            "total_expenses": total_expenses,
            "accounts": result.get("accounts", []),
            "item": result.get("item", {}),
        }

    except Exception as e:
        detail = str(e)
        status_code = 404 if "No Plaid connection" in detail else 500
        raise HTTPException(status_code=status_code, detail=detail)


@router.get("/connections", response_model=UserConnectionsResponse)
async def get_connections(user_id: str = Query(...)):
    try:
        connections = await plaid_service.get_connections_for_user(user_id)

        return UserConnectionsResponse(
            user_id=user_id,
            connections=[
                PlaidConnectionInfo(**connection)
                for connection in connections
            ],
            total=len(connections),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=PlaidStatusResponse)
async def get_status(user_id: str = Query(...)):
    try:
        connections = await plaid_service.get_connections_for_user(user_id)

        return PlaidStatusResponse(
            configured=bool(plaid_service.client_id and plaid_service.secret),
            environment=plaid_service.env,
            user_id=user_id,
            connected=len(connections) > 0,
            connection_count=len(connections),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sandbox/connect")
async def sandbox_connect(
    user_id: str = Query(...),
    institution_id: str = Query("ins_109508"),
):
    try:
        return await plaid_service.create_sandbox_token_for_user(
            user_id=user_id,
            institution_id=institution_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_connection():
    try:
        return await plaid_service.test_connection()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))