from __future__ import annotations

from typing import (
    Any,
    Generator,
    Generic,
    Iterator,
    List,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

T = TypeVar("T")  # DTO type
K = TypeVar("K", contravariant=True)  # Key type (e.g., str, int)


@runtime_checkable
class RepositoryBasePort(Generic[T, K], Protocol):
    """Generic interface (port) for basic repository operations.

    This protocol defines the standard CRUD-like operations expected from any
    persistence adapter.
    """

    def save_all(self, items: List[T]) -> None: ...

    def get_all(self) -> List[T]: ...

    def iter_all(self, batch_size: int | None = None) -> Generator[T, None, None]: ...

    def get_all_primary_keys(self) -> List[str]: ...

    def get_existing_by_columns(
        self, column_names: Union[str, List[str]]
    ) -> List[Tuple]: ...

    def iter_existing_by_columns(
        self,
        column_names: Union[str, List[str]],
        *,
        batch_size: int | None = None,
        include_nulls: bool = False,
    ) -> Iterator[Tuple]: ...

    def has_item(self, identifier: K) -> bool: ...

    def get_by_id(self, identifier: K) -> T: ...

    def get_by_column_values(
        self,
        column_names: Union[str, List[str]],
        values: Union[Any, List[Any]],
    ) -> List[T]: ...

    def get_page_after(self, last_id: int, limit: int) -> List[T]: ...

    def _safe_cast(self, value: Any) -> Union[int, str]: ...

    def _sort_key(self, obj: Any, pk_columns: Sequence) -> tuple[Union[int, str], ...]: ...
