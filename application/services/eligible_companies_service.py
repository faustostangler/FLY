"""Application service that materializes the eligible companies projection."""

from __future__ import annotations

import time
from dataclasses import replace
from datetime import datetime

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.services.eligible_companies_batch_updater_service import (
    EligibleCompaniesBatchUpdaterService,
)
from domain.dtos.eligible_companies_command_dto import EligibleCompaniesCommandDTO
from domain.dtos.eligible_companies_result_dto import EligibleCompaniesResultDTO
from domain.ports.eligible_companies_read_port import EligibleCompaniesReadPort
from domain.ports.eligible_companies_write_port import EligibleCompaniesWritePort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort


class EligibleCompaniesService:
    """Coordinates the read-model refresh using existing domain policies."""

    def __init__(
        self,
        *,
        logger: LoggerPort,
        repository_company: RepositoryCompanyDataPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        repository_stock_quote: RepositoryStockQuotePort,
        read_port: EligibleCompaniesReadPort,
        write_port: EligibleCompaniesWritePort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self._logger = logger
        self._repository_company = repository_company
        self._repository_statements_fetched = repository_statements_fetched
        self._repository_stock_quote = repository_stock_quote
        self._read_port = read_port
        self._write_port = write_port
        self._uow_factory = uow_factory
        self._batch_service = EligibleCompaniesBatchUpdaterService(logger=logger)

    def run(self, cmd: EligibleCompaniesCommandDTO) -> EligibleCompaniesResultDTO:
        start_ts = datetime.utcnow()
        perf_start = time.perf_counter()
        self._logger.log(
            "EligibleCompaniesService.start",
            level="info",
            extra={
                "version": cmd.version,
                "window_start": cmd.window_start.isoformat() if cmd.window_start else None,
                "window_end": cmd.window_end.isoformat() if cmd.window_end else None,
                "rule_params": dict(cmd.rule_params),
            },
        )

        with self._uow_factory() as uow:
            current = self._read_port.get_current(uow=uow)
            if current and current.version == cmd.version:
                self._logger.log(
                    "EligibleCompaniesService.skip_existing_version",
                    level="info",
                    extra={"version": cmd.version},
                )
                return current

            companies = self._repository_company.get_all(uow=uow)
            statement_names = self._repository_statements_fetched.get_unique_by_column(
                column_name="company_name",
                uow=uow,
            )
            quote_tickers = self._repository_stock_quote.get_unique_by_column(
                column_name="ticker",
                uow=uow,
            )

            projection = self._batch_service.build_projection(
                companies=companies,
                statement_company_names=statement_names,
                quote_tickers=quote_tickers,
            )

            result = EligibleCompaniesResultDTO(
                evaluated_count=len(companies),
                eligible_count=len(projection),
                version=cmd.version,
                started_at=start_ts,
                completed_at=datetime.utcnow(),
            )

            # Ensure DTOs carry the version that will be persisted.
            versioned_projection = [
                replace(item, projection_version=cmd.version)
                for item in projection
            ]

            self._write_port.save_projection(
                uow=uow,
                command=cmd,
                companies=versioned_projection,
                result=result,
            )
            uow.commit()

        elapsed = time.perf_counter() - perf_start
        self._logger.log(
            "EligibleCompaniesService.done",
            level="info",
            extra={
                "version": cmd.version,
                "eligible_count": result.eligible_count,
                "evaluated_count": result.evaluated_count,
                "duration_seconds": round(elapsed, 3),
            },
        )

        return result
