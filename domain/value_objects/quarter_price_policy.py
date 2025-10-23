from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from statistics import mean
from typing import Iterable, Sequence

from domain.dtos.stock_quote_dto import StockQuoteDTO


class QuarterPriceUnavailableError(RuntimeError):
    """Raised when it is not possible to derive an aggregated quarter price."""


class QuarterPriceMethod(str, Enum):
    EOP = "EOP"
    AVG_TRAD = "AVG_TRAD"


@dataclass(frozen=True)
class QuarterPricePolicy:
    """Encapsulates the business rule used to derive a quarter price."""

    method: QuarterPriceMethod = QuarterPriceMethod.EOP

    @staticmethod
    def default() -> "QuarterPricePolicy":
        return QuarterPricePolicy(method=QuarterPriceMethod.EOP)

    def aggregate(self, quotes: Sequence[StockQuoteDTO], *, quarter_end: datetime) -> tuple[float, datetime]:
        """Derive the representative price for the quarter.

        Args:
            quotes: Sequence of quotes belonging to the quarter.
            quarter_end: The last calendar day of the quarter.

        Returns:
            A tuple ``(price, asof)``.

        Raises:
            QuarterPriceUnavailableError: If there are no usable quotes.
        """

        cleaned = [q for q in quotes if q and q.date and (q.adj_close is not None or q.close is not None)]
        if not cleaned:
            raise QuarterPriceUnavailableError("No quotes available for aggregation")

        if self.method == QuarterPriceMethod.EOP:
            return self._aggregate_eop(cleaned, quarter_end=quarter_end)

        if self.method == QuarterPriceMethod.AVG_TRAD:
            return self._aggregate_avg(cleaned)

        raise QuarterPriceUnavailableError(f"Unsupported quarter price method: {self.method}")

    def _aggregate_eop(
        self, quotes: Sequence[StockQuoteDTO], *, quarter_end: datetime
    ) -> tuple[float, datetime]:
        ordered = sorted(quotes, key=lambda q: q.date)
        eligible = [q for q in ordered if q.date <= quarter_end]
        if not eligible:
            raise QuarterPriceUnavailableError("No quotes prior to quarter end")
        selected = eligible[-1]
        price = self._resolve_price(selected)
        if price is None:
            raise QuarterPriceUnavailableError("Selected quote lacks price data")
        return price, selected.date

    def _aggregate_avg(self, quotes: Sequence[StockQuoteDTO]) -> tuple[float, datetime]:
        prices: list[float] = []
        asof = None
        for quote in quotes:
            price = self._resolve_price(quote)
            if price is not None:
                prices.append(price)
                asof = quote.date
        if not prices or asof is None:
            raise QuarterPriceUnavailableError("Unable to compute average price for quarter")
        return mean(prices), asof

    @staticmethod
    def _resolve_price(quote: StockQuoteDTO) -> float | None:
        return quote.adj_close if quote.adj_close not in (None, 0) else quote.close

    def accepts(self, method: QuarterPriceMethod | str) -> bool:
        return QuarterPriceMethod(method) == self.method

    @classmethod
    def ensure(cls, policy: "QuarterPricePolicy | QuarterPriceMethod | str | None") -> "QuarterPricePolicy":
        if policy is None:
            return cls.default()
        if isinstance(policy, QuarterPricePolicy):
            return policy
        return QuarterPricePolicy(method=QuarterPriceMethod(policy))

    def allowed_methods(self) -> Iterable[str]:
        return [m.value for m in QuarterPriceMethod]
