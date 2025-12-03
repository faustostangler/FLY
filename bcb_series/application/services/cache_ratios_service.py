from __future__ import annotations

import hashlib
import inspect
from collections.abc import Mapping
from types import ModuleType
from typing import Any, Callable, Iterable

import pandas as pd

from domain.dtos.cache_ratios_context_dto import CacheRatiosContextDTO
from domain.dtos.cache_ratios_result_dto import CacheRatiosResultDTO
from domain.ports.cache_ratios_port import CacheRatiosPort


class CacheRatiosService:
    """High-level helper responsible for caching ratios computations."""

    def __init__(
        self,
        *,
        cache_port: CacheRatiosPort,
        logical_name: str = "ratios",
        version: str = '1',
    ) -> None:
        self._cache_port = cache_port
        self._logical_name = logical_name
        self._version = version
        self._cache_port.initialize()

    @staticmethod
    def build_code_hash(items: Iterable[Any]) -> str:
        """
        Calcula um hash SHA-256 determinístico a partir de uma lista de objetos
        (funções, módulos, classes ou qualquer outro Python object).

        Args:
            items: iterável de objetos a serem inspecionados.

        Returns:
            str: hash SHA-256 hexdigest.
        """
        parts: list[str] = []

        for obj in items:
            try:
                # tenta obter o source code
                src = inspect.getsource(obj)
            except (OSError, TypeError):
                try:
                    # se for módulo, tenta ler o arquivo
                    if isinstance(obj, ModuleType) and hasattr(obj, "__file__"):
                        with open(obj.__file__, "r", encoding="utf-8") as f:
                            src = f.read()
                    else:
                        # fallback: repr das chaves conhecidas
                        src = repr(sorted(vars(obj).keys()))
                except Exception:
                    src = repr(obj)

            parts.append(src)

        payload = "\n/*--SEGMENT--*/\n".join(parts).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def get_or_compute(
        self,
        *,
        company_name: str,
        quotes: Mapping[str, pd.DataFrame] | None,
        statements: Mapping[str, pd.DataFrame] | None,
        indicators: Mapping[str, pd.DataFrame] | None,
        compute_fn: Callable[[], pd.DataFrame],
        code_hash: str,
    ) -> tuple[pd.DataFrame, CacheRatiosResultDTO]:
        """Return cached ratios or compute and persist them when absent"""
        context = CacheRatiosContextDTO(
            logical_name=self._logical_name,
            version=self._version,
            quotes_hash=self._hash_mapping(quotes),
            statements_hash=self._hash_mapping(statements),
            indicators_hash=self._hash_mapping(indicators),
            code_hash=code_hash,
        )
        cache_key = context.cache_key

        cached = self._cache_port.load(cache_key)
        if cached is not None:
            df_cached, entry = cached
            return df_cached, CacheRatiosResultDTO(
                company_name=company_name,
                cache_key=cache_key,
                hit=True,
                entry=entry,
            )

        df = compute_fn()
        entry = self._cache_port.store(
            context=context,
            df=df,
            company_name=company_name,
        )
        return df, CacheRatiosResultDTO(
            company_name=company_name,
            cache_key=cache_key,
            hit=False,
            entry=entry,
        )

    def invalidate_outdated(self, *, code_hash: str) -> None:
        """Trigger a single sweep to remove outdated cache artifacts."""

        self._cache_port.invalidate_outdated(code_hash=code_hash)

    def _hash_mapping(self, data: Mapping[str, pd.DataFrame] | None) -> str:
        if not data:
            return self._empty_hash()

        parts: list[str] = []
        for key in sorted(data):
            df = data[key]
            if df is None or df.empty:
                continue
            parts.append(f"{key}:{self._hash_dataframe(df)}")

        if not parts:
            return self._empty_hash()

        payload = "|".join(parts).encode()
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _hash_dataframe(df: pd.DataFrame) -> str:
        if df is None or df.empty:
            return CacheRatiosService._empty_hash()

        normalized = df.copy()
        normalized = normalized.sort_index()
        normalized = normalized.sort_index(axis=1)

        if isinstance(normalized.index, pd.DatetimeIndex):
            normalized.index = normalized.index.tz_localize(None)

        for column in normalized.columns:
            series = normalized[column]
            if pd.api.types.is_datetime64_any_dtype(series):
                normalized[column] = pd.to_datetime(series, errors="coerce")

        hashed = pd.util.hash_pandas_object(normalized, index=True).values.tobytes()
        return hashlib.sha256(hashed).hexdigest()

    @staticmethod
    def _empty_hash() -> str:
        return hashlib.sha256(b"EMPTY").hexdigest()
