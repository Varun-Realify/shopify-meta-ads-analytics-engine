from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlaidConnectionDocument(BaseModel):
    user_id: str
    item_id: str
    access_token: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LinkTokenRequest(BaseModel):
    user_id: str


class LinkTokenResponse(BaseModel):
    link_token: str
    expiration: str
    request_id: Optional[str] = None


class ExchangeTokenRequest(BaseModel):
    user_id: str
    public_token: str


class ExchangeTokenResponse(BaseModel):
    success: bool
    item_id: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    message: str = "Bank account linked successfully"


class PlaidConnectionInfo(BaseModel):
    item_id: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserConnectionsResponse(BaseModel):
    user_id: str
    connections: List[PlaidConnectionInfo]
    total: int


class PlaidStatusResponse(BaseModel):
    configured: bool
    environment: str
    user_id: str
    connected: bool
    connection_count: int