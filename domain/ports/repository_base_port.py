from __future__ import annotations

from typing import (
    Any,
    Generic,
    Iterable,
    Iterator,
    List,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

from sqlalchemy import and_, or_

from application.ports.uow_port import Uow

# Type variable for the entity/DTO stored in the repository
T = TypeVar("T")

# Type variable for the primary key or identifier (contravariant to allow subtyping)
K = TypeVar("K", covariant=True)


@runtime_checkable
class RepositoryBasePort(Protocol, Generic[T, K]):
    """Generic interface (port) for repository operations.

    Defines the expected contract for any persistence adapter.
    The design follows a CRUD-like pattern but remains flexible
    for batch operations and column-based lookups.

    Type parameters:
        T: The entity or DTO type stored in the repository.
        K: The type of the primary key or identifier (e.g., str, int).
    """

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy model class and its PK columns.

        Subclasses must implement this to declare the ORM model associated with
        the DTO ``T`` and the tuple of primary key columns used for ordering
        and lookups.

        Returns:
            Tuple[type, tuple]: A pair ``(Model, pk_columns)`` where ``Model`` is
            the ORM class and ``pk_columns`` is an ordered tuple of SQLAlchemy
            column expressions representing the primary key.

        Raises:
            NotImplementedError: If a subclass does not override this method.
        """
        # Must be implemented by subclass to define the ORM mapping
        raise NotImplementedError

    def save_all(self, items: List[T], *, uow: Uow) -> None: ...

    def iter_existing_by_columns(
        self,
        column_names: Union[str, List[str]],
        *,
        uow: Uow,
        batch_size: int | None = None,
        include_nulls: bool = False,
        distinct: bool = False,
    ) -> Iterator[Tuple]: ...

    def get_all_by_columns(
        self,
        column_names: Union[str, List[str], Tuple[str, ...]],
        *,
        uow: Uow,
        include_nulls: bool = False,
        batch_size: int | None = None,
        distinct: bool = False,
    ) -> List[Tuple]: ...

    def get_unique_by_column(
        self,
        column_name: str,
        *,
        uow: Uow,
    ) -> List[Any]: ...

    def get_all(
        self,
        *,
        uow: Uow,
        batch_size: int | None = None,
    ) -> list[T]:...

    def get_by_column_values(
        self,
        values: Iterable[tuple[str, Any]] | dict[str, Any],
        *,
        uow: Uow,
        batch_size: int | None = None,  # opcional, apenas para manter padrão
    ) -> list[T]:...

    # def get_existing_by_columns(
    #     self, column_names: Union[str, List[str]],
    #     uow: Uow,
    # ) -> List[Tuple]: ...

    # def _safe_cast(self, value: Any) -> Union[int, str]: ...

    # def _sort_key(self, obj: Any, pk_columns: Sequence) -> tuple[Union[int, str], ...]: ...

    # def get_all(self) -> List[T]: ...

    # def iter_all(self, batch_size: int | None = None) -> Generator[T, None, None]: ...

    # def get_all_primary_keys(self) -> List[str]: ...

    # def has_item(self, identifier: K) -> bool: ...

    # def get_by_id(self, identifier: K) -> T: ...

    # def get_by_column_values(
    #     self,
    #     column_names: Union[str, List[str]],
    #     values: Union[Any, List[Any]],
    # ) -> List[T]: ...

    # def get_page_after(self, last_id: int, limit: int) -> List[T]: ...
