"""Configuration options for HTTP adapters."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HttpConfig:
    """Settings for session pooling, timeouts and throttling."""

    session_pool_size: int = 4
    timeout_connect: float = 5.0
    timeout_read: float = 20.0
    rate_per_sec: float = 2.0
    burst: int = 4
    circuit_failures: int = 3
    circuit_open_seconds: float = 20.0


def load_http_config() -> HttpConfig:
    """Return default ``HttpConfig`` instance."""

    # keep simple defaults; later this can read env or a file if desired
    return HttpConfig()
