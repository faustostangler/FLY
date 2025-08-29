from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class NSDReady:
    nsd_id: int
    version_hash: str
    occurred_at: datetime
    correlation_id: str
    schema_version: int = 1

@dataclass(frozen=True)
class StatementsFetched:
    nsd_id: int
    count: int
    occurred_at: datetime
    correlation_id: str
    schema_version: int = 1
