from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.exceptions import (
    BankApiException,
    BankPaymentNotFoundException,
    BankRequestException,
)
from src.integrations.bank.schemas import (
    AcquiringCheckRequest,
    AcquiringCheckResponse,
    AcquiringStartRequest,
    AcquiringStartResponse,
)


class BankClient:
    """Клиент для интеграции с API банка (эквайринг)."""

    async def acquiring_start(
        self,
        data: AcquiringStartRequest,
    ) -> AcquiringStartResponse:
        """
        Имитация запроса в банк на создание платежа.
        """

        try:
            if data.order_id < 1:
                raise BankRequestException('Некорректный номер заказа')

            if data.amount <= 0:
                raise BankRequestException('Некорректная сумма платежа')

            # имитация успешного ответа банка
            return AcquiringStartResponse(bank_payment_id=str(uuid4()))
        except (BankRequestException, BankPaymentNotFoundException):
            raise
        except Exception as exc:
            raise BankApiException() from exc

    async def acquiring_check(
        self,
        data: AcquiringCheckRequest,
    ) -> AcquiringCheckResponse:
        """
        Имитация запроса в банк для проверки статуса платежа.
        """

        try:
            if not data.bank_payment_id:
                raise BankRequestException(
                    'Не передан идентификатор платежа банка'
                )

            try:
                UUID(data.bank_payment_id)
            except ValueError:
                raise BankPaymentNotFoundException(data.bank_payment_id)

            # имитация успешного ответа банка
            return AcquiringCheckResponse(
                bank_payment_id=data.bank_payment_id,
                amount=Decimal('100.00'),
                bank_status='PAID',
                paid_at=datetime.now(UTC),
            )
        except (BankRequestException, BankPaymentNotFoundException):
            raise
        except Exception as exc:
            raise BankApiException() from exc
