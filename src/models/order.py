from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import BaseModel
from src.db.columns import amount_column
from src.domain.enums import OrderPaymentStatus
from src.models.payment import Payment


class Order(BaseModel):
    __tablename__ = 'orders'
    __table_args__ = (
        CheckConstraint(
            'total_amount > 0', name='ck_orders_total_amount_gt_zero'
        ),
        CheckConstraint(
            'paid_amount >= 0', name='ck_orders_paid_amount_gte_zero'
        ),
        CheckConstraint(
            'paid_amount <= total_amount',
            name='ck_orders_paid_amount_lte_total_amount',
        ),
    )

    # сумма заказа
    total_amount: Mapped[Decimal] = amount_column(nullable=False)

    # сколько уже оплачено
    paid_amount: Mapped[Decimal] = amount_column(
        default=Decimal('0.00'),
        server_default='0.00',
        nullable=False,
    )

    payment_status: Mapped[OrderPaymentStatus] = mapped_column(
        Enum(OrderPaymentStatus, name='order_payment_status'),
        default=OrderPaymentStatus.UNPAID,
        server_default='UNPAID',
        nullable=False,
    )

    # платежи заказа
    payments: Mapped[list[Payment]] = relationship(back_populates='order')
