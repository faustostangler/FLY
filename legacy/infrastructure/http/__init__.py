"""HTTP infrastructure utilities: pooling, rate limiting, circuit breaker."""

from legacy.infrastructure.http.circuit_breaker import (
    BreakerPolicy,
    CircuitBreakerScraper,
)
from legacy.infrastructure.http.rate_limiter import RateLimitedScraper, TokenBucket
from legacy.infrastructure.http.session_pool import SessionPool

__all__ = [
    "SessionPool",
    "TokenBucket",
    "RateLimitedScraper",
    "BreakerPolicy",
    "CircuitBreakerScraper",
]
