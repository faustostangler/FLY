from __future__ import annotations

import time

from infrastructure.http.rate_limiter import TokenBucket


def test_token_bucket_delays_after_burst():
    bucket = TokenBucket(rate_per_sec=2.0, burst=1)
    assert bucket.delay() == 0.0
    d = bucket.delay()
    assert d > 0.0
    time.sleep(d)
    # after waiting the suggested delay, next call should be immediate
    assert bucket.delay() == 0.0
