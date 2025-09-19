from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MarketSymbolsDTO:
    """Represents the resolved trading symbols for a company.

    Attributes:
        primary: Preferred ticker code to be used when a single symbol is
            required (e.g., for price lookups). The string is returned in the
            canonical B3 format without exchange suffixes.
        tickers: Ordered tuple with all recognized ticker codes for the
            company, already normalized to uppercase without separators.
        b3_root: Issuer root code used by B3 endpoints such as COTAHIST. This
            value usually matches the CVM "issuing_company" field and is the
            symbol required to request monthly quotation tables.
    """

    primary: str | None
    tickers: Tuple[str, ...]
    b3_root: str | None

    def has_symbol(self) -> bool:
        """Return ``True`` when a primary trading symbol is available."""

        return bool(self.primary)
