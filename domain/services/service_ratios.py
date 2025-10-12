from __future__ import annotations

from typing import Iterable, List, Sequence

from application.usecases.calculate_ratios import CalculateRatiosUseCase
from domain.dtos.ratio_result_dto import RatioResultDTO
from application.ports.logger_port import LoggerPort


class RatiosService:
    """Application service to trigger ratio computations for one or more companies."""

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
        indicator_codes: Iterable[str],
        indicator_source: str | None = None,
    ) -> List[RatioResultDTO]:
        results: List[RatioResultDTO] = []
        for company in companies:
            try:
                ratios = self._calculate(
                    company_name=company,
                    indicator_codes=indicator_codes,
                    indicator_source=indicator_source,
                )
                results.extend(ratios)
            except Exception as exc:
                self._logger.log(
                    f"Ratio computation failed for {company}: {exc}",
                    level="error",
                )
        return results
