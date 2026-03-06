from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from src.db.session import SessionFactory


class UnitOfWork:
    """Реализация паттерна Unit of Work поверх SQLAlchemy Session.

    Использование:
        with UnitOfWork() as uow:
            ... работа с uow.session ...
    """

    def __init__(
        self, session_factory: Callable[[], Session] = SessionFactory
    ):
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> UnitOfWork:
        self.session = self._session_factory()
        # Явно начинаем транзакцию.
        self.session.begin()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        assert self.session is not None
        try:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
        finally:
            self.session.close()
