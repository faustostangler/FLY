from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Iterable, List, Mapping, Sequence

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.services.indicator_normalizer_service import IndicatorNormalizerService
from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.dtos.ratio_dto import RatioRecordDTO
from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.dtos.sync_results_dto import SyncResultsDTO


class RatiosService:
    """Combine statements, stock quotes and indicators into derived ratios."""

    _DEFAULT_IPCA_CODES = {"433"}
    _DEFAULT_PROFIT_KEYWORDS = ("lucro", "net income", "resultado", "profit")

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,
        indicator_normalizer: IndicatorNormalizerService,
    ) -> None:
        self.config = config
        self.logger = logger
        self.indicator_normalizer = indicator_normalizer

        ratios_config = getattr(getattr(config, "ratios", None), "profit_price", None)
        self.ipca_codes = set(getattr(ratios_config, "ipca_codes", self._DEFAULT_IPCA_CODES))
        keywords = getattr(ratios_config, "profit_keywords", self._DEFAULT_PROFIT_KEYWORDS)
        self.profit_keywords = tuple(str(k).lower() for k in keywords)

    def __call__(
        self,
        *,
        statements: Sequence[StatementFetchedDTO] | None = None,
        stock_quotes: Sequence[StockQuoteDTO] | None = None,
        indicators: Sequence[IndicatorRecordDTO] | None = None,
    ) -> SyncResultsDTO[RatioRecordDTO]:
        return self.run(
            statements=statements or (),
            stock_quotes=stock_quotes or (),
            indicators=indicators or (),
        )

    def run(
        self,
        *,
        statements: Sequence[StatementFetchedDTO],
        stock_quotes: Sequence[StockQuoteDTO],
        indicators: Sequence[IndicatorRecordDTO],
    ) -> SyncResultsDTO[RatioRecordDTO]:
        if not stock_quotes or not statements or not indicators:
            self.logger.log(
                "RatiosService skipped: missing statements, stock quotes or indicators",
                level="warning",
            )
            return SyncResultsDTO(items=[], metrics=0)

        normalized_indicators = self.indicator_normalizer.normalize(indicators)
        ipca_series = self._build_indicator_series(normalized_indicators)
        if not ipca_series:
            self.logger.log(
                "RatiosService skipped: unable to locate IPCA indicator series",
                level="warning",
            )
            return SyncResultsDTO(items=[], metrics=0)

        profits = self._build_profit_series(statements)
        if not profits:
            self.logger.log(
                "RatiosService skipped: unable to locate profit statements",
                level="warning",
            )
            return SyncResultsDTO(items=[], metrics=0)

        quotes_by_company = defaultdict(list)
        for quote in stock_quotes:
            key = (quote.company_name or "").strip() or quote.ticker
            quotes_by_company[key].append(quote)

        ratios: List[RatioRecordDTO] = []
        for company, company_quotes in quotes_by_company.items():
            profit_timeline = profits.get(company)
            if not profit_timeline:
                continue

            profit_timeline.sort(key=lambda item: item[0])
            for quote in sorted(company_quotes, key=lambda q: q.date):
                quote_date = quote.date.date()
                price = quote.adj_close or quote.close
                if price is None or price == 0:
                    continue

                ipca_value = ipca_series.get(quote_date)
                profit_value = self._latest_before(profit_timeline, quote_date)

                if ipca_value is None or profit_value is None:
                    continue

                deflated_price = price / (ipca_value or 1.0)
                if deflated_price == 0:
                    continue

                ratio_value = profit_value / deflated_price
                ratios.append(
                    RatioRecordDTO(
                        company_name=company,
                        ticker=quote.ticker,
                        date=quote.date,
                        ratio_code="profit_ipca_price",
                        ratio_name="Profit over IPCA-deflated price",
                        value=ratio_value,
                        components={
                            "profit": profit_value,
                            "price": price,
                            "ipca": ipca_value,
                            "deflated_price": deflated_price,
                        },
                        source_indicator=next(iter(self.ipca_codes), None),
                    )
                )

        ratios.sort(key=lambda item: (item.company_name, item.ticker, item.date))
        return SyncResultsDTO(items=ratios, metrics=len(ratios))

    def _build_indicator_series(
        self, normalized: Iterable[IndicatorRecordDTO]
    ) -> Mapping[date, float]:
        series: dict[date, float] = {}
        for record in normalized:
            if record.code in self.ipca_codes or "ipca" in record.name.lower():
                series[record.observation_date.date()] = float(record.value or 0.0)
        return series

    def _build_profit_series(
        self, statements: Iterable[StatementFetchedDTO]
    ) -> Mapping[str, List[tuple[date, float]]]:
        profits: dict[str, List[tuple[date, float]]] = defaultdict(list)
        for row in statements:
            description = (row.description or "").lower()
            if not description:
                continue
            if not any(keyword in description for keyword in self.profit_keywords):
                continue

            company = (row.company_name or "").strip() or row.nsd
            profits[company].append((row.quarter.date(), float(row.value or 0.0)))
        return profits

    @staticmethod
    def _latest_before(
        items: Sequence[tuple[date, float]], target: date
    ) -> float | None:
        latest_value: float | None = None
        for item_date, value in items:
            if item_date <= target:
                latest_value = value
            else:
                break
        return latest_value
