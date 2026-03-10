from decimal import Decimal

from src.db.uow import UnitOfWork
from src.domain.exceptions import OrderNotFoundException
from src.models.order import Order
from src.schemas.order import OrderCreate


class OrderService:
    async def create_order(self, uow: UnitOfWork, data: OrderCreate) -> Order:

        async with uow:
            order = Order(
                total_amount=data.total_amount,
                paid_amount=Decimal('0.00'),
            )

            await uow.orders.create(order)

            return order

    async def get_order(self, uow: UnitOfWork, order_id: int) -> Order:
        async with uow:
            order = await uow.orders.get_by_id(order_id)

            if order is None:
                raise OrderNotFoundException(order_id)

            return order
