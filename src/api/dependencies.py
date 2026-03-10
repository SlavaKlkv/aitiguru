from typing import Any, AsyncGenerator

from src.db.uow import UnitOfWork


async def get_uow() -> AsyncGenerator[UnitOfWork, Any]:
    async with UnitOfWork() as uow:
        yield uow
