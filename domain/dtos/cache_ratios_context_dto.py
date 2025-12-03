from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, kw_only=True)
class CacheRatiosContextDTO:
    """Hashes describing the inputs used to compute ratios for caching."""

    logical_name: str
    version: str
    quotes_hash: str
    statements_hash: str
    indicators_hash: str
    code_hash: str

    @property
    def app_hash(self) -> str:
        payload = f"{self.logical_name}|{self.version}".encode()
        return hashlib.sha256(payload).hexdigest()

    @property
    def cache_key(self) -> str:
        parts: Iterable[str] = (
            self.app_hash,
            self.quotes_hash,
            self.statements_hash,
            self.indicators_hash,
            self.code_hash,
        )
        payload = "|".join(parts).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
