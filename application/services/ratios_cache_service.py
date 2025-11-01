from __future__ import annotations

import hashlib
import inspect
from collections.abc import Callable, Mapping
from typing import Any

import pandas as pd

from domain.dtos.ratios_cache_context_dto import RatiosCacheContextDTO
from domain.dtos.ratios_cache_result_dto import RatiosCacheResultDTO
from domain.ports.ratios_cache_port import RatiosCachePort


class RatiosCacheService:
    """High-level helper responsible for caching ratios computations."""

    def __init__(
        self,
        *,
        cache_port: RatiosCachePort,
        logical_name: str = "statements_ratio",
        version: int = 1,
    ) -> None:
        self._cache_port = cache_port
        self._logical_name = logical_name
        self._version = version
        self._cache_port.initialize()

    @staticmethod
    def build_code_hash(func: Callable[..., Any]) -> str:
        """Return a deterministic hash for the provided callable."""

        source = inspect.getsource(func)
        return hashlib.sha256(source.encode()).hexdigest()

    def get_or_compute(
        self,
        *,
        company_name: str,
        quotes: Mapping[str, pd.DataFrame] | None,
        statements: Mapping[str, pd.DataFrame] | None,
        indicators: Mapping[str, pd.DataFrame] | None,
        compute_fn: Callable[[], pd.DataFrame],
        code_hash: str,
    ) -> tuple[pd.DataFrame, RatiosCacheResultDTO]:
        """Return cached ratios or compute and persist them when absent."""

        context = RatiosCacheContextDTO(
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
            return df_cached, RatiosCacheResultDTO(
                company_name=company_name,
                cache_key=cache_key,
                hit=True,
                entry=entry,
            )

        self._cache_port.invalidate_outdated(code_hash=code_hash)
        df = compute_fn()
        entry = self._cache_port.store(cache_key, df, code_hash)
        return df, RatiosCacheResultDTO(
            company_name=company_name,
            cache_key=cache_key,
            hit=False,
            entry=entry,
        )

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
            return RatiosCacheService._empty_hash()

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
