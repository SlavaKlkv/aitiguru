from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_uow
from src.db.uow import UnitOfWork
from src.schemas.order import OrderCreate, OrderResponse
from src.services.orders import OrderService

router = APIRouter(prefix='/orders', tags=['orders'])
service = OrderService()


@router.post(
    '/',
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    data: OrderCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> OrderResponse:
    order = await service.create_order(uow, data)
    return OrderResponse.model_validate(order)


@router.get(
    '/{order_id}',
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
async def get_order(
    order_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> OrderResponse:
    order = await service.get_order(uow, order_id)

    return OrderResponse.model_validate(order)
