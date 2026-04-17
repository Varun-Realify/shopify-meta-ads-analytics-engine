from pydantic import BaseModel
from typing import Optional, List

class ConnectionStatus(BaseModel):
    shopify: bool
    meta: bool
    shopify_store: Optional[str] = None
    shopify_currency: Optional[str] = None
    meta_user: Optional[str] = None
    meta_ad_account: Optional[str] = None
    errors: List[str] = []
