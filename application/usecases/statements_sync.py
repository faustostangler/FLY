"""Use case responsible for synchronizing financial statements."""

from __future__ import annotations

import time
from datetime import datetime

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.usecases.statements_transformer import StatementTransformer
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.dtos.statements_sync_item_dto import StatementsSyncItemDTO
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort


class StatementsUseCase:
    """Load raw statements, normalize them and persist fetched entries."""

    def __init__(
        self,
        *,
        logger: LoggerPort,
        repository_statements_raw: RepositoryStatementsRawPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        transformer: StatementTransformer,
        uow_factory: UowFactoryPort,
    ) -> None:
        self._logger = logger
        self._repository_statements_raw = repository_statements_raw
        self._repository_statements_fetched = repository_statements_fetched
        self._transformer = transformer
        self._uow_factory = uow_factory

    def run(self) -> SyncResultsDTO[StatementsSyncItemDTO]:
        start_ts = datetime.utcnow()
        perf_start = time.perf_counter()
        self._logger.log(
            "StatementsUseCase.start",
            level="info",
            extra={"started_at": start_ts.isoformat()},
        )

        with self._uow_factory() as uow:
            raw_items = self._repository_statements_raw.get_all(uow=uow)
            transformed = [self._transformer.transform(raw) for raw in raw_items]

            if transformed:
                self._repository_statements_fetched.save_all(transformed, uow=uow)
            uow.commit()

        elapsed = time.perf_counter() - perf_start
        self._logger.log(
            "StatementsUseCase.done",
            level="info",
            extra={
                "duration_seconds": round(elapsed, 3),
                "raw_count": len(raw_items),
                "persisted_count": len(transformed),
            },
        )

        summary = [
            StatementsSyncItemDTO(source="raw", count=len(raw_items)),
            StatementsSyncItemDTO(source="fetched", count=len(transformed)),
        ]

        return SyncResultsDTO(items=summary, metrics=len(transformed))
