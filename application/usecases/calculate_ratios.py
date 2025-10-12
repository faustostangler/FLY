from __future__ import annotations

from itertools import chain
from typing import Mapping, Sequence

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.services.daily_series_normalizer_service import DailySeriesNormalizerService
from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.dtos.ratio_result_dto import RatioResultDTO
from domain.ports.repository_ratios_port import RepositoryRatiosPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
# <<<<<<< codex/create-standalone-ratioservice-for-ratios-calculation-ot39np
from domain.services.ratio_domain_service import RatioDomainService
# =======
# from domain.services.ratio_service import RatioService
# >>>>>>> 2025-10-11-Ratios


class CalculateRatiosUseCase:
    """Orchestrate calendar normalization and ratio computation for a company."""

    def __init__(
        self,
        *,
        logger: LoggerPort,
        normalizer: DailySeriesNormalizerService,
# <<<<<<< codex/create-standalone-ratioservice-for-ratios-calculation-ot39np
        ratio_service: RatioDomainService,
# x=======
#         ratio_service: RatioService,
# >>>>>>> 2025-10-11-Ratios
        repository_statements: RepositoryStatementFetchedPort,
        repository_quotes: RepositoryStockQuotePort,
        repository_ratios: RepositoryRatiosPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self._logger = logger
        self._normalizer = normalizer
        self._ratio_service = ratio_service
        self._repository_statements = repository_statements
        self._repository_quotes = repository_quotes
        self._repository_ratios = repository_ratios
        self._uow_factory = uow_factory

    def __call__(
        self,
        *,
        company_name: str,
        indicators: Mapping[str, Sequence[IndicatorRecordDTO]],
    ) -> Sequence[RatioResultDTO]:
        return self.run(
            company_name=company_name,
            indicators=indicators,
        )

    def run(
        self,
        *,
        company_name: str,
        indicators: Mapping[str, Sequence[IndicatorRecordDTO]],
    ) -> Sequence[RatioResultDTO]:
        self._logger.log(
            f"Calculating ratios for {company_name}",
            level="info",
        )

        statements = self._repository_statements.get_by_company_name(company_name)
        quotes = self._repository_quotes.get_by_company_name(company_name)

        bundle = self._normalizer.normalize(
            company_id=company_name,
            statements=statements,
            quotes=quotes,
            indicators=indicators,
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
