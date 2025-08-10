"""Processor for fetching financial statement rows."""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from domain.ports import ConfigPort
from domain.ports.scraper_ports import RawStatementScraperPort
from application.usecases.fetch_statements import FetchStatementsUseCase
from domain.dto import NsdDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import (
    LoggerPort,
    WorkerPoolPort, 
    MetricsCollectorPort,
    NSDRepositoryPort,
    SqlAlchemyCompanyDataRepositoryPort,
    SqlAlchemyParsedStatementRepositoryPort,
    SqlAlchemyRawStatementRepositoryPort,
)

from .base_processor import BaseProcessor


class FetchStatementsProcessor(
    BaseProcessor[
        Tuple[
            List[NsdDTO],
            Optional[Callable[[List[RawStatementDTO]], None]],
            Optional[int],
        ],  # TypeVar("L")
        List[Tuple[NsdDTO, List[RawStatementDTO]]],  # TypeVar("T")
        List[Tuple[NsdDTO, List[RawStatementDTO]]],  # TypeVar("P")
    ]
):
    """Fetch raw statements for pending NSDs."""

    def __init__(
        self,
        logger: LoggerPort,
        config: ConfigPort,
        source: RawStatementScraperPort,
        company_repo: SqlAlchemyCompanyDataRepositoryPort,
        nsd_repo: NSDRepositoryPort,
        raw_statement_repo: SqlAlchemyRawStatementRepositoryPort,
        parsed_statements_repo: SqlAlchemyParsedStatementRepositoryPort,
        metrics_collector: MetricsCollectorPort,
        worker_pool_executor: WorkerPoolPort,
        max_workers: int = 1,
    ) -> None:
        """Store dependencies for the processor."""
        self.logger = logger
        self.config = config
        self.source = source
        self.company_repo = company_repo
        self.nsd_repo = nsd_repo
        self.raw_statement_repo = raw_statement_repo
        self.parsed_statements_repo = parsed_statements_repo
        self.collector = metrics_collector
        self.worker_pool_executor = worker_pool_executor
        self.max_workers = max_workers

        self.fetch_usecase = FetchStatementsUseCase(
            logger=self.logger,
            config=self.config,
            source=source,
            raw_statement_repository=raw_statement_repo,
            parsed_statements_repo=parsed_statements_repo,
            metrics_collector=self.collector,
            worker_pool_executor=self.worker_pool_executor,
            max_workers=self.max_workers,
        )

    def _build_targets(self) -> List[NsdDTO]:
        """Return NSD identifiers that still need fetching."""
        company_records = self.company_repo.get_all()
        nsd_records = self.nsd_repo.get_all()
        if not company_records or not nsd_records:
            return []
        nsd_rows_processed = {
            row[0]
            for row in self.raw_statement_repo.get_existing_by_columns(
                column_names="nsd"
            )
        }
        valid_types = set(self.config.domain.statements_types)
        company_names = {c.company_name for c in company_records if c.company_name}
        nsd_company_names = {n.company_name for n in nsd_records if n.company_name}
        common_company_names = set(company_names.intersection(nsd_company_names))
        results = self.nsd_repo.get_all_pending(
            company_names=common_company_names,
            valid_types=valid_types,
            exclude_nsd=nsd_rows_processed,
        )
        return results

    def run(
        self,
        save_callback: Optional[Callable[[List[RawStatementDTO]], None]] = None,
        threshold: Optional[int] = None,
    ) -> List[Tuple[NsdDTO, List[RawStatementDTO]]]:
        """Run the fetch pipeline."""
        return super().run(save_callback=save_callback, threshold=threshold)

    def load(
        self,
        save_callback: Optional[Callable[[List[RawStatementDTO]], None]] = None,
        threshold: Optional[int] = None,
    ) -> Tuple[
        List[NsdDTO], Optional[Callable[[List[RawStatementDTO]], None]], Optional[int]
    ]:
        """Prepare targets and forward optional persistence parameters."""
        targets = self._build_targets()
        return targets, save_callback, threshold

    def transform(
        self,
        data: Tuple[
            List[NsdDTO],
            Optional[Callable[[List[RawStatementDTO]], None]],
            Optional[int],
        ],
    ) -> List[Tuple[NsdDTO, List[RawStatementDTO]]]:
        """Fetch statement rows for ``targets`` using the use case."""
        targets, save_callback, threshold = data
        if not targets:
            return []
        return self.fetch_usecase.fetch_statement_rows(
            batch_rows=targets, save_callback=save_callback, threshold=threshold
        )

    def persist(
        self, data: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[Tuple[NsdDTO, List[RawStatementDTO]]]:
        """No-op persist step; the use case already saves rows."""
        return data
