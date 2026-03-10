from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.routers.orders import router as order_router
from src.api.routers.payments import router as payment_router
from src.domain.exceptions import DomainException

app = FastAPI(
    title='Payments API', description='Сервис для работы с платежами по заказу'
)


@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail': exc.detail},
    )


main_router = APIRouter(prefix='/api')

for router in (payment_router, order_router):
    main_router.include_router(router)

app.include_router(main_router)


@app.get('/health', tags=['system'])
def health():
    return {'status': 'ok'}
