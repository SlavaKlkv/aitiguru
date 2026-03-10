from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AcquiringStartRequest(BaseModel):
    order_id: int
    amount: Decimal


class AcquiringStartResponse(BaseModel):
    bank_payment_id: str | None = None
    error: str | None = None


class AcquiringCheckRequest(BaseModel):
    bank_payment_id: str


class AcquiringCheckResponse(BaseModel):
    bank_payment_id: str | None = None
    amount: Decimal | None = None
    bank_status: str | None = None
    paid_at: datetime | None = None
    error: str | None = None
