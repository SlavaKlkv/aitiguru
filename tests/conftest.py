"""Тесты гоняются на in-memory SQLite: Postgres для них не нужен.

`SELECT … FOR UPDATE` SQLite игнорирует, поэтому проверить блокировку строки
здесь нельзя — всё остальное поведение сервиса воспроизводится один в один.
"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5432')
os.environ.setdefault('POSTGRES_USER', 'postgres')
os.environ.setdefault('POSTGRES_PASSWORD', 'postgres')
os.environ.setdefault('POSTGRES_DB', 'postgres')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///:memory:')

from src.api.dependencies import get_uow  # noqa: E402
from src.db.base import Base  # noqa: E402
from src.db.uow import UnitOfWork  # noqa: E402
from src.main import app  # noqa: E402


@pytest_asyncio.fixture
async def session_factory() -> AsyncGenerator[
    async_sessionmaker[AsyncSession], None
]:
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )

    yield factory

    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_uow() -> AsyncGenerator[UnitOfWork, None]:
        async with UnitOfWork(session_factory=session_factory) as uow:
            yield uow

    app.dependency_overrides[get_uow] = override_get_uow

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def order(client):
    """Фабрика заказов: создаёт заказ и отдаёт его тело ответа."""

    async def _create(total_amount: str = '1000.00') -> dict:
        response = await client.post(
            '/api/orders/', json={'total_amount': total_amount}
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _create
