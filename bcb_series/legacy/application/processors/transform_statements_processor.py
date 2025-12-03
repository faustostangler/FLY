"""Processor to batch-transform fetched statements into metrics."""

from __future__ import annotations

from typing import List

from application.usecases.transform_statements import TransformStatementsUseCase
from domain.dto.statement_fetched_dto import StatementFetchedDTO
from domain.ports import ConfigPort, LoggerPort, RepositoryStatementFetchedPort
from domain.services import StatementClassificationService
from infrastructure.transformers import (
    IntelStatementTransformerAdapter,
    MathStatementTransformerAdapter,
)

from .base_processor import BaseProcessor


class TransformStatementsProcessor(BaseProcessor):
    """Transform fetched statement rows and persist the results."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        fetched_repo: RepositoryStatementFetchedPort,
    ) -> None:
        """Create processor with repository and configuration."""
        self.logger = logger
        self.fetched_repo = fetched_repo

        math_transformer = MathStatementTransformerAdapter(config)
        classification_service = StatementClassificationService()
        intel_transformer = IntelStatementTransformerAdapter(
            config=config, classification_service=classification_service
        )
        self.transform_usecase = TransformStatementsUseCase(
            math_transformer=math_transformer,
            intel_transformer=intel_transformer,
            config=config,
            logger=self.logger,
        )

    def load(
        self, fetched_groups: List[List[StatementFetchedDTO]]
    ) -> List[List[StatementFetchedDTO]]:
        """Forward fetched groups to the transformation stage."""
        return fetched_groups

    def transform(
        self, data: List[List[StatementFetchedDTO]]
    ) -> List[List[StatementFetchedDTO]]:
        """Apply the transformation use case to each group."""
        processed: List[List[StatementFetchedDTO]] = []
        for group in data:
            try:
                processed.append(self.transform_usecase.execute(group))
                self.logger.info(f"Processed group of {len(group)} statements")
            except Exception as exc:  # pragma: no cover - log and continue
                self.logger.error(f"Error processing group: {exc}")
        return processed

    def persist(
        self, data: List[List[StatementFetchedDTO]]
    ) -> List[List[StatementFetchedDTO]]:
        """Persist transformed statements to the repository."""
        for group in data:
            self.fetched_repo.save_all(group)
        return data

    def run(
        self, data: List[List[StatementFetchedDTO]]
    ) -> List[List[StatementFetchedDTO]]:
        """Run the transformation pipeline."""
        return super().run(data)
