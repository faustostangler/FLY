# infrastructure/http/builders.py
from __future__ import annotations
from application.ports.config_port import ConfigPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.logger_port import LoggerPort
from infrastructure.http.cloudscraper_affinity_http_client import CloudscraperAffinityHttpClient
from infrastructure.http.circuit_breaker import CircuitBreakerClient, BreakerPolicy
from infrastructure.http.rate_limiter import RateLimitedClient, TokenBucket

def build_http_client(config: ConfigPort, logger: LoggerPort) -> AffinityHttpClientPort:
    # base com sessão compartilhável, headers sorteados, pool e cache condicional
    base = CloudscraperAffinityHttpClient(config.database.connection_string, logger)
    # rate limit global simples: 5 req/s com burst 10
    limited = RateLimitedClient(base, TokenBucket(rate_per_sec=5.0, burst=10), logger)
    # circuit breaker para 429/403
    wrapped = CircuitBreakerClient(limited, logger, BreakerPolicy(failure_threshold=3, open_seconds=20.0))
    return wrapped
