from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricsDTO:
    """Execution metrics for worker pools."""

    elapsed_time: float
    network_bytes: int = 0
    processing_bytes: int = 0
    failures: int = 0
