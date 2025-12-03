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
        try:
            session: Session = self._session_factory()
            uow = _SqlAlchemyUoW(session)
            try:
                yield uow
            except Exception as e:
                uow.rollback()
                raise
            finally:
                if session.in_transaction():
                    try:
                        session.rollback()
                    except Exception:
                        pass
                session.close()
        except Exception as e:
            pass

class _SqlAlchemyUoW(Uow):
    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        if self._session.in_transaction():
            self._session.commit()

    def rollback(self) -> None:
        if self._session.in_transaction():
            try:
                self._session.rollback()
            except Exception:
                pass

