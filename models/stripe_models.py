from pydantic import BaseModel
from typing import List, Optional

class StripeTransaction(BaseModel):
    """Represents a single payment record gathered from Stripe."""
    id: str
    amount: float
    currency: str
    receipt: Optional[str] = None
    status: str
    created: str
    customer_name: Optional[str] = None

class StripeHistoryResponse(BaseModel):
    """Structured response for the payment history dashboard."""
    user_id: str
    total_transactions: int
    data: List[StripeTransaction]