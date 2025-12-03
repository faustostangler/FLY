from __future__ import annotations

from typing import Any, ContextManager, Protocol, runtime_checkable


@runtime_checkable
class Uow(Protocol):
    @property
    def session(self) -> Any:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


@runtime_checkable
class UowFactoryPort(Protocol):
    """Fábrica que retorna um context manager de UoW, ex.: with uow_factory() as uow: ..."""

    def __call__(self) -> ContextManager[Uow]:
        ...
