# Payments

Сервис оплаты заказов. Заказ можно закрыть одним платежом или десятью,
наличными или картой, часть денег вернуть — и в любой момент сказать, сколько
по заказу реально оплачено.

## Главное правило

Статус заказа никто не выставляет руками. Он выводится из суммы успешных
платежей и пересчитывается при каждом изменении:

| Оплачено | Статус заказа |
| --- | --- |
| ничего | `UNPAID` |
| часть суммы | `PARTIALLY_PAID` |
| вся сумма | `PAID` |

Поэтому расхождение «платежи говорят одно, статус — другое» здесь невозможно
в принципе, а не «не должно случаться».

Сам платёж живёт своей жизнью: `CREATED → PENDING → PAID`, плюс терминальные
`REFUNDED` и `FAILED`. Наличные (`CASH`) закрываются сразу, эквайринг
(`ACQUIRING`) уходит в `PENDING` и ждёт банк.

## Слои

```mermaid
flowchart LR
  A["API · FastAPI<br/>routers"] --> B["Services<br/>бизнес-логика"]
  B --> C["Repositories<br/>доступ к данным"]
  B --> D["BankClient<br/>эквайринг"]
  C --> E[("PostgreSQL")]
  B -. "commit / rollback" .-> F["Unit of Work"]
  F --> C
```

| Слой | Что делает | Где |
| --- | --- | --- |
| API | эндпоинты, коды ответов, валидация запроса | [`src/api`](src/api) |
| Сервисы | сценарии оплаты, возврата, сверки с банком | [`src/services`](src/services) |
| Репозитории | запросы к БД, никакой бизнес-логики | [`src/repos`](src/repos) |
| Интеграции | клиент банковского API | [`src/integrations/bank`](src/integrations/bank) |
| Домен | статусы, доменные исключения, константы | [`src/domain`](src/domain) |
| Модели и схемы | ORM SQLAlchemy 2 и Pydantic-схемы | [`src/models`](src/models), [`src/schemas`](src/schemas) |

Сервисы не трогают сессию напрямую: транзакцией управляет Unit of Work
([`src/db/uow.py`](src/db/uow.py)). Он открывает её на запрос и коммитит одним
куском — платёж и пересчитанный статус заказа сохраняются вместе либо не
сохраняются вовсе.

`BankClient` — имитация банка: проверяет входные данные и отвечает
правдоподобно, чтобы сценарии эквайринга проходились целиком без реального
провайдера. Контракт вынесен в
[`integrations/bank/schemas.py`](src/integrations/bank/schemas.py), так что живой
HTTP-клиент подставляется без правок сервисного слоя.

Схема БД — [`docs/database/diagram.png`](docs/database/diagram.png).

## Запуск

```bash
git clone https://github.com/SlavaKlkv/payments.git
cd payments
cp .env.example .env

docker compose up --build
```

Compose поднимает PostgreSQL 17, накатывает миграции Alembic и стартует
приложение. Swagger UI — <http://127.0.0.1:8000/docs>.

На хосте, без Docker:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
cp .env.local.example .env        # то же, но POSTGRES_HOST=localhost

uv run alembic upgrade head
uv run uvicorn src.main:app --reload --port 8000
```

Новая миграция после правки моделей:
`uv run alembic revision --autogenerate -m "..."`.

## Эндпоинты

| Метод | Путь | Что делает |
| --- | --- | --- |
| `POST` | `/orders/` | создать заказ |
| `GET` | `/orders/{order_id}` | заказ с текущим статусом оплаты |
| `POST` | `/payments/` | платёж по заказу: `CASH` или `ACQUIRING` |
| `POST` | `/payments/{payment_id}/refund` | возврат |
| `POST` | `/payments/{payment_id}/check` | спросить банк о статусе и синхронизировать |

```bash
# заказ на 1000
curl -sX POST http://127.0.0.1:8000/orders/ \
  -H 'Content-Type: application/json' \
  -d '{"total_amount": "1000.00"}'

# 400 наличными — заказ станет PARTIALLY_PAID
curl -sX POST http://127.0.0.1:8000/payments/ \
  -H 'Content-Type: application/json' \
  -d '{"order_id": 1, "amount": "400.00", "payment_type": "CASH"}'
```

Точные схемы запросов и ответов — в Swagger на `/docs`.

Стек: Python 3.13, FastAPI, SQLAlchemy 2 (async), Pydantic, Alembic,
PostgreSQL 17, uv, Docker Compose.

## Лицензия

MIT
