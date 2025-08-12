"""Processor for fetching financial statement rows."""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from application.usecases.fetch_statements import FetchStatementsUseCase
from domain.dto import NsdDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import (
    CompanyDataRepositoryPort,
    ConfigPort,
    LoggerPort,
    MetricsCollectorPort,
    NSDRepositoryPort,
    ParsedStatementRepositoryPort,
    RawStatementRepositoryPort,
    WorkerPoolPort,
)
from domain.ports.scraper_ports import RawStatementScraperPort

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
        company_repo: CompanyDataRepositoryPort,
        nsd_repo: NSDRepositoryPort,
        raw_statement_repo: RawStatementRepositoryPort,
        parsed_statements_repo: ParsedStatementRepositoryPort,
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
        company_names = {
            c.company_name for c in self.company_repo.iter_all() if c.company_name
        }
        if not company_names:
            return []

        nsd_rows_processed = {
            row[0] for row in self.raw_statement_repo.iter_existing_by_columns("nsd")
        }
        valid_types = set(self.config.domain.statements_types)

        results: List[NsdDTO] = []
        for nsd in self.nsd_repo.iter_all():
            if (
                nsd.company_name
                and nsd.company_name in company_names
                and nsd.nsd_type in valid_types
                and nsd.nsd not in nsd_rows_processed
            ):
                results.append(nsd)

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
