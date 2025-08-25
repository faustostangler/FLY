"""Processor for parsing raw statement rows."""

from __future__ import annotations

from typing import List, Tuple

from application.usecases.parse_and_classify_statements import (
    ParseAndClassifyStatementsUseCase,
)
from domain.dto import NsdDTO, StatementParsedDTO, WorkerTaskDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import (
    ConfigPort,
    LoggerPort,
    MetricsCollectorPort,
    RepositoryStatementParsedPort,
    WorkerPoolPort,
)

from .base_processor import BaseProcessor


class ParseStatementsProcessor(BaseProcessor):
    """Parse raw statement rows and persist cleaned records."""

    def __init__(
        self,
        logger: LoggerPort,
        repository: RepositoryStatementParsedPort,
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
        self, data: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[List[StatementParsedDTO]]:
        tasks = list(enumerate(data))

        def processor(task: WorkerTaskDTO) -> List[StatementParsedDTO]:
            _nsd, rows = task.data
            return [self.parse_usecase.parse_and_store_row(r) for r in rows]

        result = self.worker_pool_executor.run(
            tasks=tasks, processor=processor, logger=self.logger
        )
        return result.items

    def load(
        self, fetched: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[Tuple[NsdDTO, List[RawStatementDTO]]]:
        """Simply forward fetched rows to the pipeline."""
        return fetched

    def transform(
        self, data: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[List[StatementParsedDTO]]:
        """Parse fetched rows in parallel."""
        if not data:
            return []
        return self._parse_all(data)

    def persist(
        self, data: List[List[StatementParsedDTO]]
    ) -> List[List[StatementParsedDTO]]:
        """Finalize parse use case and return parsed data."""
        self.parse_usecase.finalize()
        return data

    def run(
        self, fetched: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[List[StatementParsedDTO]]:
        """Run the parse pipeline."""
        
        results: List[List[StatementParsedDTO]] = self._parse_all(fetched)
        return results
