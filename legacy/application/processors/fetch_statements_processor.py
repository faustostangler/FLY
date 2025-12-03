"""Processor for fetching financial statement rows."""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple, TypeAlias

from application.usecases.fetch_statements import FetchStatementsUseCase
from domain.dto import NsdDTO
from domain.dto.statement_raw_dto import StatementRawDTO
from domain.ports import (
    RepositoryCompanyDataPort,
    ConfigPort,
    LoggerPort,
    MetricsCollectorPort,
    RepositoryNsdPort,
    RepositoryStatementFetchedPort,
    StatementRawRepositoryPort,
    WorkerPoolPort,
)
from domain.ports.scraper_ports import StatementsRawcraperPort

from .base_processor import BaseProcessor


LoadPayload: TypeAlias = Tuple[
    List[NsdDTO],
    Optional[Callable[[List[StatementRawDTO]], None]],
    Optional[int],
]
RowsByNsd: TypeAlias = List[Tuple[NsdDTO, List[StatementRawDTO]]]
PersistedPayload: TypeAlias = RowsByNsd


class FetchStatementsProcessor(BaseProcessor[LoadPayload, RowsByNsd, PersistedPayload]):
    """Fetch raw statements for pending NSDs."""

    def __init__(
        self,
        logger: LoggerPort,
        config: ConfigPort,
        source: StatementsRawcraperPort,
        company_repo: RepositoryCompanyDataPort,
        nsd_repo: RepositoryNsdPort,
        raw_statement_repo: StatementRawRepositoryPort,
        fetched_statements_repo: RepositoryStatementFetchedPort,
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
        self.fetched_statements_repo = fetched_statements_repo
        self.collector = metrics_collector
        self.worker_pool_executor = worker_pool_executor
        self.max_workers = max_workers

        self.fetch_usecase = FetchStatementsUseCase(
            logger=self.logger,
            config=self.config,
            source=source,
            raw_statement_repository=raw_statement_repo,
            fetched_statements_repo=fetched_statements_repo,
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

        raw_statement_rows_with_nsd_processed = {
            int(row[0])
            for row in self.raw_statement_repo.iter_existing_by_columns("nsd")
        }
        valid_types = set(self.config.domain.statements_types)

        results: List[NsdDTO] = []
        for nsd in self.nsd_repo.iter_all():
            if (
                nsd.company_name
                and nsd.company_name in company_names
                and nsd.nsd_type in valid_types
                and nsd.nsd not in raw_statement_rows_with_nsd_processed
            ):
                results.append(nsd)
        results.sort(key=lambda nsd: (nsd.company_name, nsd.quarter, nsd.version))

        return results

    def run(
        self,
        save_callback: Optional[Callable[[List[StatementRawDTO]], None]] = None,
        threshold: Optional[int] = None,
    ) -> RowsByNsd:
        """Run the fetch pipeline."""
        data: LoadPayload = self.load(save_callback=save_callback, threshold=threshold)
        transformed: RowsByNsd = self.transform(data)
        result: PersistedPayload = self.persist(transformed)
        return result

    def load(
        self,
        save_callback = None,
        threshold = None,
    ) -> Tuple[
        List[NsdDTO], Optional[Callable[[List[StatementRawDTO]], None]], Optional[int]
    ]:
        """Prepare targets and forward optional persistence parameters."""
        targets = self._build_targets()
        return targets, save_callback, threshold

    def transform(
        self,
        data: Tuple[
            List[NsdDTO],
            Optional[Callable[[List[StatementRawDTO]], None]],
            Optional[int],
        ],
    ) -> PersistedPayload:
        """Fetch statement rows for ``targets`` using the use case."""
        targets, save_callback, threshold = data
        if not targets:
            return []
        return self.fetch_usecase.fetch_statement_rows(
            batch_rows=targets, save_callback=save_callback, threshold=threshold
        )

    def persist(
        self, data: PersistedPayload
    ) -> PersistedPayload:
        """No-op persist step; the use case already saves rows."""
        return data

