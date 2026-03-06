from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import BaseModel
from src.db.columns import amount_column
from src.domain.enums import OrderPaymentStatus
from src.models.payment import Payment


class Order(BaseModel):
    __tablename__ = 'orders'

    # сумма заказа
    total_amount: Mapped[Decimal] = amount_column(nullable=False)

    # сколько уже оплачено
    paid_amount: Mapped[Decimal] = amount_column(default=0, nullable=False)

    # статус оплаты
    payment_status: Mapped[OrderPaymentStatus] = mapped_column(
        Enum(OrderPaymentStatus, name='order_payment_status'),
        default=OrderPaymentStatus.UNPAID,
        server_default='UNPAID',
        nullable=False,
    )

    # платежи заказа
    payments: Mapped[list[Payment]] = relationship(back_populates='order')
