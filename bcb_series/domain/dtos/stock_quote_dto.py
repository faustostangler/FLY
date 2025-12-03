from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass(frozen=True, kw_only=True)
class StockQuoteDTO:
    """
    """

    id: Optional[int] = None
    company_name: str
    ticker: str
    date: datetime
    open: Optional[float]
    low: Optional[float]
    high: Optional[float]
    close: Optional[float]
    adj_close: Optional[float]
    volume: Optional[int]
    currency: Optional[str]

    @staticmethod
    def from_dict(raw: dict[str, Any], *, cleandate: Callable[[object], datetime]) -> Optional[StockQuoteDTO]:
        """Build an ``DTO`` from a raw scraped dictionary.

        Args:
            raw (dict): Dictionary containing external fields.

        Returns:
            Optional[DTO]: A fully initialized ``DTO`` if valid,
            otherwise ``None`` when input is empty.

        Raises:
            ValueError: If the field is missing or not a valid integer.
        """
        # Ensure input is not empty
        if not raw:
            return None

        # # Validate NSD field before conversion
        # nsd_raw = raw.get("nsd")
        # if nsd_raw is None or not str(nsd_raw).isdigit():
        #     raise ValueError("Invalid NSD value")

        # Build DTO from sanitized input
        return StockQuoteDTO(
            company_name=str(raw.get("company_name") or ""),
            ticker=str(raw.get("ticker") or ""),
            date=cleandate(raw.get("date") or ""),
            open=float(raw.get("oen") or 0.0),
            high=float(raw.get("high") or 0.0),
            low=float(raw.get("low") or 0.0),
            close=float(raw.get("close") or 0.0),
            adj_close=float(raw.get("adj_close") or 0.0),
            volume=int(raw.get("volume") or 0.0),
            currency=str(raw.get("currency") or "BRL"),
        )

    @staticmethod
    def from_raw(raw: StockQuoteDTO) -> StockQuoteDTO:
        """Build an ``DTO`` from another DTO-like object.

        Args:
            raw (DTO): A DTO-like object with matching attributes.

        Returns:
            DTO: A new immutable ``DTO`` instance populated
            with the same values as the input.
        """
        return StockQuoteDTO(
            id=getattr(raw, "id", None),
            company_name=getattr(raw, "company_name", ""),
            ticker=getattr(raw, "ticker", ""),
            date=getattr(raw, "date", datetime.min),
            open=getattr(raw, "open", 0.0),
            high=getattr(raw, "high", 0.0),
            low=getattr(raw, "low", 0.0),
            close=getattr(raw, "close", 0.0),
            adj_close=getattr(raw, "adj_close", 0.0),
            volume=getattr(raw, "volume", 0),
            currency=getattr(raw, "currency", "BRL"),
        )
