# infrastructure/http/backoff.py
from __future__ import annotations

import random
import time


def sleep_expo_jitter(attempt: int, base: float = 0.5, cap: float = 8.0) -> None:
    # backoff exponencial com jitter completo
    delay = min(cap, (2 ** (attempt - 1)) * base)
    delay = random.uniform(0, delay)
    time.sleep(delay)
