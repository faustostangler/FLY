# domain/utils/specs.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Protocol, Mapping, Union
import pandas as pd
import numpy as np

# Nós imutáveis
class Spec(Protocol):
    def accept(self, v: "PandasVisitor", df: pd.DataFrame) -> pd.Series: ...

@dataclass(frozen=True)
class And(Spec):
    items: tuple[Spec, ...]
    def accept(self, v, df): return v.visit_and(self, df)

@dataclass(frozen=True)
class Or(Spec):
    items: tuple[Spec, ...]
    def accept(self, v, df): return v.visit_or(self, df)

@dataclass(frozen=True)
class Not(Spec):
    item: Spec
    def accept(self, v, df): return v.visit_not(self, df)

@dataclass(frozen=True)
class Cmp(Spec):
    field: str
    op: str       # "==", "!=", ">", ">=", "<", "<=", "in", "nin", "between"
    value: Any    # escalar, sequência, ou (low, high)
    def accept(self, v, df): return v.visit_cmp(self, df)

@dataclass(frozen=True)
class StrMatch(Spec):
    field: str
    mode: str     # "contains", "startswith", "endswith", "regex"
    pattern: str
    case: bool = True
    na: bool = False
    def accept(self, v, df): return v.visit_str(self, df)

@dataclass(frozen=True)
class NullCheck(Spec):
    field: str
    negate: bool = False  # False -> isnull, True -> notnull
    def accept(self, v, df): return v.visit_null(self, df)

@dataclass(frozen=True)
class ListAny(Spec):
    """Para colunas JSON list (e.g., ticker_codes)."""
    field: str
    op: str       # "contains", "in", "overlap"
    value: Any
    def accept(self, v, df): return v.visit_list_any(self, df)
