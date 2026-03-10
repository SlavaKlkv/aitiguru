from decimal import Decimal

from src.db.uow import UnitOfWork
from src.domain.enums import OrderPaymentStatus, PaymentType
from src.domain.exceptions import (
    OrderNotFoundException,
    OverpaymentException,
    PaymentNotFoundException,
)
from src.models.payment import Payment


class PaymentService:
    @staticmethod
    def _update_order_payment_status(order) -> None:
        if order.paid_amount == 0:
            order.payment_status = OrderPaymentStatus.UNPAID
        elif order.paid_amount < order.total_amount:
            order.payment_status = OrderPaymentStatus.PARTIALLY_PAID
        else:
            order.payment_status = OrderPaymentStatus.PAID

    async def deposit(
        self,
        uow: UnitOfWork,
        order_id: int,
        amount: Decimal,
        payment_type: PaymentType,
    ) -> Payment:

        async with uow:
            order = await uow.orders.get_by_id_for_update(order_id)

            if order is None:
                raise OrderNotFoundException(order_id)

            if order.paid_amount + amount > order.total_amount:
                raise OverpaymentException()

            payment = Payment(
                order_id=order_id,
                amount=amount,
                payment_type=payment_type,
            )

            await uow.payments.add(payment)

            order.paid_amount += amount

            self._update_order_payment_status(order)

            return payment

    async def refund(
        self,
        uow: UnitOfWork,
        payment_id: int,
    ) -> Payment:

        async with uow:
            payment = await uow.payments.get_by_id(payment_id)

            if payment is None:
                raise PaymentNotFoundException(payment_id)

            order = await uow.orders.get_by_id_for_update(payment.order_id)

            if order is None:
                raise OrderNotFoundException(payment.order_id)

            order.paid_amount -= payment.amount

            self._update_order_payment_status(order)

            await uow.session.delete(payment)

            return payment
