from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_uow
from src.db.uow import UnitOfWork
from src.schemas.payment import PaymentCreate, PaymentResponse
from src.services.payments import PaymentService

router = APIRouter(prefix='/payments', tags=['payments'])
service = PaymentService()


@router.post(
    '/',
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    data: PaymentCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> PaymentResponse:
    """Создание платежа с типами CASH или ACQUIRING"""

    payment = await service.deposit(
        uow=uow,
        order_id=data.order_id,
        amount=data.amount,
        payment_type=data.payment_type,
    )

    return PaymentResponse.model_validate(payment)


@router.post(
    '/{payment_id}/refund',
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def refund_payment(
    payment_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> PaymentResponse:
    payment = await service.refund(uow=uow, payment_id=payment_id)

    return PaymentResponse.model_validate(payment)
