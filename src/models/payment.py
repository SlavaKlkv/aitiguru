from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import BaseModel
from src.db.columns import amount_column
from src.domain.constants import (
    BANK_PAYMENT_ID_LENGTH,
    BANK_STATUS_LENGTH,
)
from src.domain.enums import PaymentStatus, PaymentType

if TYPE_CHECKING:
    from src.models.order import Order


class Payment(BaseModel):
    __tablename__ = 'payments'
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_payments_amount_gt_zero'),
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey('orders.id'),
        nullable=False,
        index=True,
    )

    order: Mapped[Order] = relationship(back_populates='payments')

    amount: Mapped[Decimal] = amount_column(nullable=False)

    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType, name='payment_type'),
        nullable=False,
    )

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name='payment_status'),
        default=PaymentStatus.CREATED,
        server_default=PaymentStatus.CREATED.value,
        nullable=False,
    )

    # идентификатор платежа на стороне банка (только для эквайринга)
    bank_payment_id: Mapped[str | None] = mapped_column(
        String(BANK_PAYMENT_ID_LENGTH),
        nullable=True,
        unique=True,
    )

    # сырой статус банка
    bank_status: Mapped[str | None] = mapped_column(
        String(BANK_STATUS_LENGTH),
        nullable=True,
    )

    # время подтверждения оплаты банком
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
