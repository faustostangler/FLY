# domain/ports/uow_port.py
from types import TracebackType
from typing import Optional, Protocol, Type


class UnitOfWorkPort(Protocol):
    def __enter__(self) -> "UnitOfWorkPort": ...

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> Optional[bool]: ...

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
