from __future__ import annotations

from typing import Protocol, ContextManager, runtime_checkable


@runtime_checkable
class UnitOfWork(Protocol):
    """Contrato mínimo de UoW. Camada de aplicação orquestra, infra implementa."""
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


@runtime_checkable
class UnitOfWorkFactoryPort(Protocol):
    """Fábrica que retorna um context manager de UoW, ex.: with uow_factory() as uow: ..."""
    def __call__(self) -> ContextManager[UnitOfWork]: ...
