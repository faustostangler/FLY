"""CLI controller orchestrating the high level data pipeline."""

from __future__ import annotations

import time
from datetime import datetime

from application.services.eligible_companies_service import EligibleCompaniesService
from application.usecases.statements_sync import StatementsUseCase
from domain.services.service_ratios import RatiosService
from domain.dtos import SyncResultsDTO
from domain.dtos.eligible_companies_command_dto import EligibleCompaniesCommandDTO
from domain.dtos.eligible_companies_result_dto import EligibleCompaniesResultDTO
from domain.dtos.statements_sync_item_dto import StatementsSyncItemDTO
from infrastructure.utils.byte_formatter import ByteFormatter
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort


class Cli:
    """Thin presentation layer that orchestrates the sequential pipeline."""

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,
        statements_use_case: StatementsUseCase,
        eligible_companies_service: EligibleCompaniesService,
        ratios_service: RatiosService,
    ) -> None:
        self._config = config
        self._logger = logger
        self._statements_use_case = statements_use_case
        self._eligible_companies_service = eligible_companies_service
        self._ratios_service = ratios_service
        self._formatter = ByteFormatter()

    def __call__(self) -> None:
        self.run()

    def run(self) -> None:
        """Execute statements -> eligible -> ratios pipeline."""

        self._logger.log("Start FLY", level="info")
        total_metrics = 0
        ratios_result: SyncResultsDTO | None = None

        try:
            statements_result = self._run_statements_phase()
            total_metrics += statements_result.metrics
        except Exception as exc:  # noqa: BLE001
            self._logger.log(
                "Statements phase failed",
                level="error",
                extra={"error": str(exc)},
            )
            raise

        try:
            eligible_result = self._run_eligible_phase(statements_result)
        except Exception as exc:  # noqa: BLE001
            self._logger.log(
                "Eligible companies phase failed",
                level="error",
                extra={"error": str(exc)},
            )
            raise

        if eligible_result.eligible_count == 0:
            self._logger.log(
                "Eligible companies projection is empty; skipping ratios phase",
                level="warning",
            )
            return

        try:
            ratios_result = self._run_ratios_phase()
            total_metrics += ratios_result.metrics
        except Exception as exc:  # noqa: BLE001
            self._logger.log(
                "Ratios normalization failed",
                level="error",
                extra={"error": str(exc)},
            )
            raise

        if total_metrics > 0:
            self._logger.log(
                f"Total Download: {self._formatter.format_bytes(total_metrics)}",
                level="info",
            )

    # Internal helpers ---------------------------------------------------------
    def _run_statements_phase(self) -> SyncResultsDTO[StatementsSyncItemDTO]:
        start = time.perf_counter()
        result = self._statements_use_case.run()
        duration = time.perf_counter() - start
        self._logger.log(
            "Statements phase completed",
            level="info",
            extra={
                "duration_seconds": round(duration, 3),
                "metrics_bytes": self._formatter.format_bytes(result.metrics),
            },
        )
        return result

    def _run_eligible_phase(
        self,
        statements_result: SyncResultsDTO[StatementsSyncItemDTO],
    ) -> EligibleCompaniesResultDTO:
        start = time.perf_counter()
        command = self._build_command(statements_result)
        result = self._eligible_companies_service.run(command)
        duration = time.perf_counter() - start
        self._logger.log(
            "Eligible companies phase completed",
            level="info",
            extra={
                "duration_seconds": round(duration, 3),
                "eligible": result.eligible_count,
                "evaluated": result.evaluated_count,
                "version": result.version,
            },
        )
        return result

    def _run_ratios_phase(self) -> SyncResultsDTO:
        start = time.perf_counter()
        result = self._ratios_service.run()
        duration = time.perf_counter() - start
        if result.items:
            self._logger.log(
                "Ratios phase completed",
                level="info",
                extra={
                    "duration_seconds": round(duration, 3),
                    "cache_entries": len(result.items),
                    "metrics_bytes": self._formatter.format_bytes(result.metrics),
                },
            )
        else:
            self._logger.log(
                "Ratios phase skipped",
                level="warning",
                extra={"duration_seconds": round(duration, 3)},
            )
        return result

    def _build_command(
        self,
        statements_result: SyncResultsDTO[StatementsSyncItemDTO],
    ) -> EligibleCompaniesCommandDTO:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        version = f"{self._config.fly_settings.version}:{timestamp}"
        rule_params = {
            "recency_year": getattr(self._config.domain, "recency_year", None),
            "raw_count": next((item.count for item in statements_result.items if item.source == "raw"), 0),
        }
        return EligibleCompaniesCommandDTO(
            version=version,
            rule_params={k: v for k, v in rule_params.items() if v is not None},
        )
