from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import PaymentStatus
from src.models.payment import Payment


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, payment: Payment) -> None:
        self.session.add(payment)

    async def get_by_id(self, payment_id: int) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def list_by_order_id(self, order_id: int) -> list[Payment]:
        """Получить все платежи по заказу."""
        result = await self.session.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return list(result.scalars().all())

    async def pending_amount(self, order_id: int) -> Decimal:
        """Сумма платежей заказа, ожидающих подтверждения банком."""
        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.order_id == order_id,
                Payment.status == PaymentStatus.PENDING,
            )
        )
        return Decimal(str(result.scalar_one()))
