from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from src.domain.constants import AMOUNT_PRECISION, AMOUNT_SCALE, ORDER_ID_MIN
from src.domain.enums import PaymentType


class PaymentBase(BaseModel):
    order_id: int = Field(ge=ORDER_ID_MIN)
    amount: Decimal = Field(
        decimal_places=AMOUNT_SCALE,
        max_digits=AMOUNT_PRECISION,
        examples=['100.00'],
    )
    payment_type: PaymentType


class PaymentCreate(PaymentBase):
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {
                    'order_id': 1,
                    'amount': '100.00',
                    'payment_type': 'ACQUIRING',
                }
            ]
        }
    )


class PaymentResponse(PaymentBase):
    id: int = Field(examples=[1])

    @field_serializer('amount')
    def serialize_amount(self, value: Decimal) -> str:
        return f'{value:.2f}'

    model_config = ConfigDict(from_attributes=True)
