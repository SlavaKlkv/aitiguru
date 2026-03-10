from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import SessionFactory
from src.repos.order import OrderRepository
from src.repos.payment import PaymentRepository


class UnitOfWork:
    """Реализация паттерна Unit of Work поверх AsyncSession."""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession] = SessionFactory,
    ) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None
        self.orders: OrderRepository | None = None
        self.payments: PaymentRepository | None = None

    async def __aenter__(self) -> UnitOfWork:
        self.session = self._session_factory()
        self.orders = OrderRepository(self.session)
        self.payments = PaymentRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        assert self.session is not None
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()
