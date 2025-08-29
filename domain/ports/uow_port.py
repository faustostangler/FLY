# domain/ports/uow_port.py
from typing import Protocol, ContextManager


class UnitOfWorkPort(Protocol, ContextManager["UnitOfWorkPort"]):
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
