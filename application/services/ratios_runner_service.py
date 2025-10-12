from __future__ import annotations

from typing import List, Mapping, Sequence

from application.ports.logger_port import LoggerPort
from application.usecases.calculate_ratios import CalculateRatiosUseCase
from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.dtos.ratio_result_dto import RatioResultDTO


class RatiosRunnerService:
    """Trigger ratio computations for a list of companies within the application layer."""

    def __init__(
        self,
        *,
        logger: LoggerPort,
        calculate_usecase: CalculateRatiosUseCase,
    ) -> None:
        self._logger = logger
        self._calculate = calculate_usecase

    def run(
        self,
        companies: Sequence[str],
        *,
        indicators: Mapping[str, Sequence[IndicatorRecordDTO]],
    ) -> List[RatioResultDTO]:
        results: List[RatioResultDTO] = []
        for company in companies:
            try:
                ratios = self._calculate(
                    company_name=company,
                    indicators=indicators,
                )
                results.extend(ratios)
            except Exception as exc:
                self._logger.log(
                    f"Ratio computation failed for {company}: {exc}",
                    level="error",
                )
        return results
