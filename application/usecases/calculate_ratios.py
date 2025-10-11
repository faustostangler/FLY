from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.services.daily_series_normalizer_service import DailySeriesNormalizerService
from domain.dtos.ratio_result_dto import RatioResultDTO
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_ratios_port import RepositoryRatiosPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.services.ratio_service import RatioService


class CalculateRatiosUseCase:
    """Orchestrate calendar normalization and ratio computation for a company."""

    def __init__(
        self,
        *,
        logger: LoggerPort,
        normalizer: DailySeriesNormalizerService,
        ratio_service: RatioService,
        repository_statements: RepositoryStatementFetchedPort,
        repository_quotes: RepositoryStockQuotePort,
        repository_indicators: RepositoryIndicatorsPort,
        repository_ratios: RepositoryRatiosPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self._logger = logger
        self._normalizer = normalizer
        self._ratio_service = ratio_service
        self._repository_statements = repository_statements
        self._repository_quotes = repository_quotes
        self._repository_indicators = repository_indicators
        self._repository_ratios = repository_ratios
        self._uow_factory = uow_factory

    def __call__(
        self,
        *,
        company_name: str,
        start_date: datetime,
        end_date: datetime,
        indicator_codes: Iterable[str],
        indicator_source: str | None = None,
    ) -> Sequence[RatioResultDTO]:
        return self.run(
            company_name=company_name,
            start_date=start_date,
            end_date=end_date,
            indicator_codes=indicator_codes,
            indicator_source=indicator_source,
        )

    def run(
        self,
        *,
        company_name: str,
        start_date: datetime,
        end_date: datetime,
        indicator_codes: Iterable[str],
        indicator_source: str | None = None,
    ) -> Sequence[RatioResultDTO]:
        self._logger.log(
            f"Calculating ratios for {company_name} between {start_date.date()} and {end_date.date()}",
            level="info",
        )

        statements = self._repository_statements.get_by_company_and_period(
            company_name,
            start=start_date,
            end=end_date,
        )
        quotes = self._repository_quotes.get_by_company_and_period(
            company_name,
            start=start_date,
            end=end_date,
        )
        indicators = self._repository_indicators.get_by_codes_and_period(
            source=indicator_source,
            codes=indicator_codes,
            start=start_date,
            end=end_date,
        )

        bundle = self._normalizer.normalize(
            company_id=company_name,
            statements=statements,
            quotes=quotes,
            indicators=indicators,
            start_date=start_date,
            end_date=end_date,
        )

        ratios = self._ratio_service.calculate(bundle)
        filtered = [ratio for ratio in ratios if ratio.value is not None]

        with self._uow_factory() as uow:
            self._repository_ratios.save_all(filtered, uow=uow)

        self._logger.log(
            f"Computed {len(filtered)} ratio points for {company_name}",
            level="info",
        )
        return filtered
