# application/ports/price_lookup_port.py

from typing import Protocol, Optional
from datetime import date


class PriceLookupPort(Protocol):
    def price_at_quarter_end(self, symbol: str, quarter_end: date) -> Optional[float]: ...
