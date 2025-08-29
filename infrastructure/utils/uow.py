# infrastructure/uow/sqlalchemy_uow.py
from contextlib import AbstractContextManager
from sqlalchemy.orm import Session

class SqlAlchemyUnitOfWork(AbstractContextManager):
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self):
        self.session = self._session_factory()
        return self

    def __exit__(self, exc_type, *_):
        try:
            assert self.session is not None
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            assert self.session is not None
            self.session.close()

    # compat com port
    def commit(self):
        assert self.session is not None
        self.session.commit()

    def rollback(self):
        assert self.session is not None
        self.session.rollback()
