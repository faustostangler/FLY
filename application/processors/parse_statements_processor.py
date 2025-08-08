"""Processor for parsing raw statement rows."""

from __future__ import annotations

from typing import List, Tuple

from application.usecases.parse_and_classify_statements import (
    ParseAndClassifyStatementsUseCase,
)
from domain.dto import NsdDTO, ParsedStatementDTO, WorkerTaskDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import ConfigPort, LoggerPort, SqlAlchemyParsedStatementRepositoryPort
from infrastructure.helpers import MetricsCollector, WorkerPool

from .base_processor import BaseProcessor


class ParseStatementsProcessor(BaseProcessor):
    """Parse raw statement rows and persist cleaned records."""

    def __init__(
        self,
        logger: LoggerPort,
        repository: SqlAlchemyParsedStatementRepositoryPort,
        config: ConfigPort,
        max_workers: int = 1,
    ) -> None:
        """Store dependencies for the processor."""
        self.logger = logger
        self.config = config
        self.max_workers = max_workers
        self.parse_usecase = ParseAndClassifyStatementsUseCase(
            logger=self.logger, repository=repository, config=self.config
        )

    def _parse_all(
        self, fetched: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[List[ParsedStatementDTO]]:
        collector = MetricsCollector()
        parse_pool = WorkerPool(
            config=self.config,
            metrics_collector=collector,
            max_workers=self.max_workers,
        )
        tasks = list(enumerate(fetched))

        def processor(task: WorkerTaskDTO) -> List[ParsedStatementDTO]:
            _nsd, rows = task.data
            return [self.parse_usecase.parse_and_store_row(r) for r in rows]

        result = parse_pool.run(tasks=tasks, processor=processor, logger=self.logger)
        return result.items

    def load(
        self, fetched: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[Tuple[NsdDTO, List[RawStatementDTO]]]:
        """Simply forward fetched rows to the pipeline."""
        return fetched

    def transform(
        self, fetched: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[List[ParsedStatementDTO]]:
        """Parse fetched rows in parallel."""
        if not fetched:
            return []
        return self._parse_all(fetched)

    def persist(
        self, parsed: List[List[ParsedStatementDTO]]
    ) -> List[List[ParsedStatementDTO]]:
        """Finalize parse use case and return parsed data."""
        self.parse_usecase.finalize()
        return parsed

    def run(
        self, fetched: List[Tuple[NsdDTO, List[RawStatementDTO]]]
    ) -> List[List[ParsedStatementDTO]]:
        """Run the parse pipeline."""
        return super().run(fetched)
