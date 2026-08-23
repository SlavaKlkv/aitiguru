from fastapi import APIRouter, FastAPI

from src.api.routers.orders import router as order_router
from src.api.routers.payments import router as payment_router
from src.domain.exceptions import init_exception_handlers

app = FastAPI(
    title='Payments API', description='Сервис для работы с платежами по заказу'
)

init_exception_handlers(app)


main_router = APIRouter(prefix='/api')

for router in (payment_router, order_router):
    main_router.include_router(router)

app.include_router(main_router)


@app.get('/health', tags=['system'])
def health():
    return {'status': 'ok'}
