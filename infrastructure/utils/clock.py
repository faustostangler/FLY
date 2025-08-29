# infrastructure/utils/clock.py
from datetime import datetime, timezone

class UtcClock:
    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)
