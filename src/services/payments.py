from datetime import UTC, datetime
from decimal import Decimal

from src.db.uow import UnitOfWork
from src.domain.enums import (
    BankPaymentStatus,
    OrderPaymentStatus,
    PaymentStatus,
    PaymentType,
)
from src.domain.exceptions import (
    BankRequestException,
    OrderNotFoundException,
    OverpaymentException,
    PaymentNotFoundException,
    RefundNotAllowedException,
)
from src.integrations.bank.client import BankClient
from src.integrations.bank.schemas import (
    AcquiringCheckRequest,
    AcquiringStartRequest,
)
from src.models.payment import Payment


class PaymentService:
    def __init__(self, bank_client: BankClient | None = None) -> None:
        self.bank_client = bank_client or BankClient()

    @staticmethod
    def _update_order_payment_status(order) -> None:
        if order.paid_amount == 0:
            order.payment_status = OrderPaymentStatus.UNPAID
        elif order.paid_amount < order.total_amount:
            order.payment_status = OrderPaymentStatus.PARTIALLY_PAID
        else:
            order.payment_status = OrderPaymentStatus.PAID

    @classmethod
    def _confirm(cls, order, payment: Payment) -> None:
        """Учесть платёж в заказе: деньги дошли."""

        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.now(UTC)
        order.paid_amount += payment.amount
        cls._update_order_payment_status(order)

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

            # незавершённый эквайринг ещё не в paid_amount, но деньги
            # по нему уже обещаны — иначе заказ можно «оплатить» дважды
            pending = await uow.payments.pending_amount(order_id)

            if order.paid_amount + pending + amount > order.total_amount:
                raise OverpaymentException()

            payment = Payment(
                order_id=order_id,
                amount=amount,
                payment_type=payment_type,
            )

            if payment_type == PaymentType.ACQUIRING:
                bank_response = await self.bank_client.acquiring_start(
                    AcquiringStartRequest(
                        order_id=order_id,
                        amount=amount,
                    )
                )
                payment.bank_payment_id = bank_response.bank_payment_id
                payment.bank_status = BankPaymentStatus.CREATED.value
                # банк ещё не подтвердил оплату: заказ не трогаем
                payment.status = PaymentStatus.PENDING
            else:
                self._confirm(order, payment)

            await uow.payments.add(payment)

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

            if payment.status != PaymentStatus.PAID:
                raise RefundNotAllowedException(
                    'Вернуть можно только оплаченный платёж, '
                    f'текущий статус — {payment.status.value}'
                )

            order = await uow.orders.get_by_id_for_update(payment.order_id)

            if order is None:
                raise OrderNotFoundException(payment.order_id)

            order.paid_amount -= payment.amount

            self._update_order_payment_status(order)

            # платёж не удаляется: возврат — это событие в истории заказа,
            # а не отсутствие платежа
            payment.status = PaymentStatus.REFUNDED

            return payment

    async def check_bank_payment(
        self,
        uow: UnitOfWork,
        payment_id: int,
    ) -> Payment:
        """
        Проверить статус банковского платежа
        и синхронизировать его с системой.
        """

        async with uow:
            payment = await uow.payments.get_by_id(payment_id)

            if payment is None:
                raise PaymentNotFoundException(payment_id)

            if payment.bank_payment_id is None:
                raise BankRequestException(
                    'Платёж не связан с банковским эквайрингом'
                )

            bank_response = await self.bank_client.acquiring_check(
                AcquiringCheckRequest(
                    bank_payment_id=payment.bank_payment_id,
                )
            )

            payment.bank_status = bank_response.bank_status

            # повторная проверка уже учтённого платежа ничего не меняет
            if payment.status != PaymentStatus.PENDING:
                return payment

            if bank_response.bank_status == BankPaymentStatus.PAID.value:
                order = await uow.orders.get_by_id_for_update(payment.order_id)

                if order is None:
                    raise OrderNotFoundException(payment.order_id)

                self._confirm(order, payment)

            elif bank_response.bank_status == BankPaymentStatus.FAILED.value:
                payment.status = PaymentStatus.FAILED

            return payment
