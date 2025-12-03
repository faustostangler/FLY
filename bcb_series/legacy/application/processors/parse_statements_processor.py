"""Processor for parsing raw statement rows."""

from __future__ import annotations

from typing import List, Tuple

from application.usecases.parse_and_classify_statements import (
    ParseAndClassifyStatementsUseCase,
)
from domain.dto import NsdDTO, StatementFetchedDTO, WorkerTaskDTO
from domain.dto.statement_raw_dto import StatementRawDTO
from domain.ports import (
    ConfigPort,
    LoggerPort,
    MetricsCollectorPort,
    RepositoryStatementFetchedPort,
    WorkerPoolPort,
)

from .base_processor import BaseProcessor


class ParseStatementsProcessor(BaseProcessor):
    """Parse raw statement rows and persist cleaned records."""

    def __init__(
        self,
        logger: LoggerPort,
        repository: RepositoryStatementFetchedPort,
        config: ConfigPort,
        worker_pool_executor: WorkerPoolPort,
        metrics_collector: MetricsCollectorPort,
        max_workers: int = 1,
    ) -> None:
        """Store dependencies for the processor."""
        self.logger = logger
        self.config = config
        self.max_workers = max_workers
        self.worker_pool_executor = worker_pool_executor
        self.collector = metrics_collector
        self.parse_usecase = ParseAndClassifyStatementsUseCase(
            logger=self.logger, repository=repository, config=self.config
        )

    def _parse_all(
        self, data: List[Tuple[NsdDTO, List[StatementRawDTO]]]
    ) -> List[List[StatementFetchedDTO]]:
        tasks = list(enumerate(data))

        def processor(task: WorkerTaskDTO) -> List[StatementFetchedDTO]:
            _nsd, rows = task.data
            return [self.parse_usecase.parse_and_store_row(r) for r in rows]

        result = self.worker_pool_executor.run(
            tasks=tasks, processor=processor, logger=self.logger
        )
        return result.items

    def load(
        self, fetched: List[Tuple[NsdDTO, List[StatementRawDTO]]]
    ) -> List[Tuple[NsdDTO, List[StatementRawDTO]]]:
        """Simply forward fetched rows to the pipeline."""
        return fetched

    def transform(
        self, data: List[Tuple[NsdDTO, List[StatementRawDTO]]]
    ) -> List[List[StatementFetchedDTO]]:
        """Parse fetched rows in parallel."""
        if not data:
            return []
        return self._parse_all(data)

    def persist(
        self, data: List[List[StatementFetchedDTO]]
    ) -> List[List[StatementFetchedDTO]]:
        """Finalize parse use case and return fetched data."""
        self.parse_usecase.finalize()
        return data

    def run(
        self, fetched: List[Tuple[NsdDTO, List[StatementRawDTO]]]
    ) -> List[List[StatementFetchedDTO]]:
        """Run the parse pipeline."""
        
        results: List[List[StatementFetchedDTO]] = self._parse_all(fetched)
        return results
