from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True, kw_only=True)
class RatiosCacheContextDTO:
    """Hashes describing the inputs used to compute ratios for caching."""

    logical_name: str
    version: int
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
        payload = (
            f"{self.app_hash}{self.quotes_hash}{self.statements_hash}{self.indicators_hash}{self.code_hash}".encode()
        )
        return hashlib.sha256(payload).hexdigest()
