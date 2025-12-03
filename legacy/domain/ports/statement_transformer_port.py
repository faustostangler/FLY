"""Port for transforming raw statement rows into fetched ones."""

from __future__ import annotations

from typing import List, Protocol, Sequence, TypeVar

T_in = TypeVar("T_in", contravariant=True)
T_out = TypeVar("T_out")


class StatementTransformerPort(Protocol[T_in, T_out]):
    def transform(self, rows: Sequence[T_in]) -> List[T_out]: ...
