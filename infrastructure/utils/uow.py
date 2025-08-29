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
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self.session.close()

    # compat com port
    def commit(self): self.session.commit()
    def rollback(self): self.session.rollback()
