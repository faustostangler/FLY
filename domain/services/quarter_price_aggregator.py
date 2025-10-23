from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from application.ports.uow_port import Uow
from domain.dtos.quarter_price_dto import QuarterPriceDTO
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_quarter_price_port import RepositoryQuarterPricePort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.value_objects import QuarterPriceMethod, QuarterPricePolicy, QuarterPriceUnavailableError


@dataclass(slots=True)
class QuarterPriceAggregator:
    """Aggregates daily quotes into a quarterly price snapshot."""

    stock_quote_repository: RepositoryStockQuotePort
    quarter_price_repository: RepositoryQuarterPricePort
    default_policy: QuarterPricePolicy = QuarterPricePolicy.default()

    def __call__(
        self,
        *,
        company_name: str,
        quarter: datetime,
        policy: QuarterPricePolicy | QuarterPriceMethod | str | None = None,
        uow: Uow,
    ) -> QuarterPriceDTO:
        return self.aggregate(
            company_name=company_name,
            quarter=quarter,
            policy=policy,
            uow=uow,
        )

    def aggregate(
        self,
        *,
        company_name: str,
        quarter: datetime,
        policy: QuarterPricePolicy | QuarterPriceMethod | str | None = None,
        uow: Uow,
    ) -> QuarterPriceDTO:
        policy_obj = QuarterPricePolicy.ensure(policy or self.default_policy)
        start, end = self._quarter_boundaries(quarter)

        quotes = list(
            self.stock_quote_repository.list_between_dates(
            company_name=company_name,
            start=start,
            end=end,
            uow=uow,
        )
        )
        if not quotes:
            raise QuarterPriceUnavailableError(
                f"No quotes found for {company_name} between {start.date()} and {end.date()}"
            )

        price, asof = policy_obj.aggregate(quotes, quarter_end=end)
        currency = self._resolve_currency(quotes, asof)

        existing = self.quarter_price_repository.get_for_quarter(
            company_name=company_name,
            quarter=end,
            method=policy_obj.method.value,
            uow=uow,
        )

        next_version = 1
        if existing is not None:
            if (
                existing.price == price
                and existing.asof == asof
                and existing.currency == currency
            ):
                return existing
            next_version = (existing.version or 0) + 1

        dto = QuarterPriceDTO(
            id=existing.id if existing else None,
            company_name=company_name,
            quarter=end,
            method=policy_obj.method.value,
            price=price,
            asof=asof,
            currency=currency,
            version=next_version,
        )

        saved = self.quarter_price_repository.insert_or_update(dto, uow=uow)
        return saved

    @staticmethod
    def _quarter_boundaries(quarter_end: datetime) -> tuple[datetime, datetime]:
        quarter_end = QuarterPriceAggregator._normalize_date(quarter_end)
        quarter_start_month = ((quarter_end.month - 1) // 3) * 3 + 1
        quarter_start = quarter_end.replace(month=quarter_start_month, day=1)
        return quarter_start, quarter_end

    @staticmethod
    def _normalize_date(raw: datetime) -> datetime:
        return raw.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _resolve_currency(quotes: list[StockQuoteDTO], asof: datetime) -> Optional[str]:
        for quote in reversed(quotes):
            if quote.date == asof and quote.currency:
                return quote.currency
        for quote in reversed(quotes):
            if quote.currency:
                return quote.currency
        return None
