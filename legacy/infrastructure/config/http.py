"""Configuration options for HTTP adapters."""

from dataclasses import dataclass, field

SESSION_POOL_SIZE = 4
TIMEOUT_CONNECT = 5.0
TIMEOUT_READ = 20.0
RATE_PER_SEC = 2.0
BURST = 4
CIRCUIT_FAILURES = 3
CIRCUIT_OPEN_SECONDS = 20.0

# Retry
RETRIES = 5  # número máximo de tentativas (incluindo a inicial)
BACKOFF_FACTOR = 0.4  # fator multiplicador para o tempo de espera entre tentativas. Ex.: 0.4 → espera 0.4s, depois 0.8s, 1.6s…
STATUS_FORCELIST = [429, 500, 502, 503, 504]  # lista de códigos HTTP que disparam nova tentativa (ex.: 429 ou 5xx).
RESPECT_RETRY_AFTER_HEADER = True  # respeitar o cabeçalho Retry-After se presente  

# HTTPAdapter
POOL_CONNECTIONS = 8  # número máximo de conexões persistentes por host que o pool mantém abertas.
POOL_MAXSIZE = 32  # número total máximo de conexões que o pool pode manter simultaneamente.


@dataclass(frozen=True)
class HttpConfig:
    """Settings for session pooling, timeouts and throttling."""

    session_pool_size: int = SESSION_POOL_SIZE
    timeout_connect: float = TIMEOUT_CONNECT
    timeout_read: float = TIMEOUT_READ
    rate_per_sec: float = RATE_PER_SEC
    burst: int = BURST
    circuit_failures: int = CIRCUIT_FAILURES
    circuit_open_seconds: float = CIRCUIT_OPEN_SECONDS
    retries: int = RETRIES
    backoff_factor: float = BACKOFF_FACTOR
    status_forcelist: list[int] = field(default_factory=lambda: STATUS_FORCELIST.copy())
    respect_retry_after_header: bool = RESPECT_RETRY_AFTER_HEADER
    pool_connections: int = POOL_CONNECTIONS
    pool_maxsize: int = POOL_MAXSIZE


def load_http_config() -> HttpConfig:
    """Return default ``HttpConfig`` instance."""

    # keep simple defaults; later this can read env or a file if desired
    return HttpConfig()
