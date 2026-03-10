from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from src.domain.constants import AMOUNT_PRECISION, AMOUNT_SCALE
from src.domain.enums import OrderPaymentStatus


class OrderBase(BaseModel):
    total_amount: Decimal = Field(
        decimal_places=AMOUNT_SCALE,
        max_digits=AMOUNT_PRECISION,
        examples=['100.00'],
    )


class OrderCreate(OrderBase):
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {
                    'total_amount': '100.00',
                }
            ]
        }
    )


class OrderResponse(OrderBase):
    id: int
    paid_amount: Decimal = Field(
        decimal_places=AMOUNT_SCALE,
        max_digits=AMOUNT_PRECISION,
        examples=['0.00'],
    )
    payment_status: OrderPaymentStatus

    @field_serializer('paid_amount')
    def serialize_amount(self, value: Decimal) -> str:
        return f'{value:.2f}'

    model_config = ConfigDict(from_attributes=True)
