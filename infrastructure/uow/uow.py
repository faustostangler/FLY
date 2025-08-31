# infrastructure/uow/sqlalchemy_uow.py
from __future__ import annotations
from contextlib import contextmanager
from sqlalchemy.orm import Session
from application.ports.uow_port import Uow, UowFactoryPort

class UowFactory(UowFactoryPort):
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    @contextmanager
    def __call__(self):
        session: Session = self._session_factory()
        uow = _SqlAlchemyUoW(session)
        try:
            yield uow
        except Exception:
            uow.rollback()
            raise
        finally:
            session.close()

class _SqlAlchemyUoW(Uow):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._txn = session.begin()

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        self._txn.commit()

    def rollback(self) -> None:
        try:
            self._txn.rollback()
        except Exception:
            pass

