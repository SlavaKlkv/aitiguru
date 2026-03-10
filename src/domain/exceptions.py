from typing import Any

import structlog
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger(__name__)


class DomainException(Exception):
    """Базовое доменное исключение."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = 'Ошибка бизнес-логики'

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


class OrderNotFoundException(DomainException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Заказ не найден'

    def __init__(self, order_id: int | None = None):
        msg = (
            'Заказ не найден'
            if order_id is None
            else f'Заказ с ID {order_id} не найден'
        )
        super().__init__(msg)


class OrderAlreadyExistsException(DomainException):
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, field: str = 'id'):
        super().__init__(f'Заказ с таким {field} уже существует')


class PaymentNotFoundException(DomainException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Платёж не найден'

    def __init__(self, payment_id: int | None = None):
        msg = (
            'Платёж не найден'
            if payment_id is None
            else f'Платёж с ID {payment_id} не найден'
        )
        super().__init__(msg)


class IntegrityConflictException(DomainException):
    status_code = status.HTTP_409_CONFLICT
    detail = 'Нарушение целостности данных'


class OverpaymentException(DomainException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = 'Сумма платежа превышает сумму заказа'


class RefundNotAllowedException(DomainException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = 'Возврат платежа невозможен'


class PermissionDenied(DomainException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = 'Доступ запрещён'


class TooManyAttempts(DomainException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = 'Слишком много попыток, попробуйте позже'


# ============================== Регистрация обработчиков =====================


def _sanitize_errors(errors: Any) -> Any:
    if isinstance(errors, dict):
        return {k: _sanitize_errors(v) for k, v in errors.items()}
    if isinstance(errors, list):
        return [_sanitize_errors(e) for e in errors]
    if isinstance(errors, tuple):
        return tuple(_sanitize_errors(e) for e in errors)
    if isinstance(errors, BaseException):
        return str(errors)
    return errors


def _json_error(
    status_code: int, detail: str, *, errors: Any | None = None
) -> JSONResponse:
    payload: dict[str, Any] = {'detail': detail}
    if errors is not None:
        payload['errors'] = errors
    return JSONResponse(
        status_code=status_code, content=jsonable_encoder(payload)
    )


def init_exception_handlers(app):
    # --- helpers for DB errors (PostgreSQL SQLSTATE) ---
    def _pg_err_info(exc: IntegrityError) -> tuple[int, str]:
        code = getattr(getattr(exc, 'orig', None), 'pgcode', None)
        status_code = status.HTTP_400_BAD_REQUEST
        message = 'Нарушение целостности данных'
        if code == '23505':
            status_code = status.HTTP_409_CONFLICT
            message = 'Нарушение уникальности'
        elif code == '23503':
            status_code = status.HTTP_400_BAD_REQUEST
            message = 'Нарушение внешнего ключа'
        elif code == '23502':
            status_code = status.HTTP_400_BAD_REQUEST
            message = 'Обязательное поле не заполнено'
        elif code == '23514':
            status_code = status.HTTP_400_BAD_REQUEST
            message = 'Нарушение ограничения CHECK'
        return status_code, message

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return _json_error(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, exc: RequestValidationError
    ):
        return _json_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            'Некорректные данные запроса',
            errors=_sanitize_errors(exc.errors()),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: ValidationError
    ):
        return _json_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            'Ошибка валидации данных',
            errors=_sanitize_errors(exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        return _json_error(exc.status_code, str(exc.detail))

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        status_code, message = _pg_err_info(exc)
        return _json_error(status_code, message)

    @app.exception_handler(DBAPIError)
    async def dbapi_error_handler(request: Request, exc: DBAPIError):
        logger.error(
            'Ошибка базы данных',
            path=str(request.url.path),
            method=request.method,
            exception=str(exc),
            exc_info=exc,
        )

        return _json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            'Ошибка базы данных',
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            'Непредвиденная ошибка',
            path=str(request.url.path),
            method=request.method,
            exception=str(exc),
            exc_info=exc,
        )

        return _json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            'Произошла непредвиденная ошибка',
        )
