"""Processor to batch-transform parsed statements into metrics."""

from __future__ import annotations

from typing import List

from application.usecases.transform_statements import TransformStatementsUseCase
from domain.dto.parsed_statement_dto import StatementParsedDTO
from domain.ports import ConfigPort, LoggerPort, RepositoryStatementParsedPort
from domain.services import StatementClassificationService
from infrastructure.transformers import (
    IntelStatementTransformerAdapter,
    MathStatementTransformerAdapter,
)

from .base_processor import BaseProcessor


class TransformStatementsProcessor(BaseProcessor):
    """Transform parsed statement rows and persist the results."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        parsed_repo: RepositoryStatementParsedPort,
    ) -> None:
        """Create processor with repository and configuration."""
        self.logger = logger
        self.parsed_repo = parsed_repo

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
        self, parsed_groups: List[List[StatementParsedDTO]]
    ) -> List[List[StatementParsedDTO]]:
        """Forward parsed groups to the transformation stage."""
        return parsed_groups

    def transform(
        self, data: List[List[StatementParsedDTO]]
    ) -> List[List[StatementParsedDTO]]:
        """Apply the transformation use case to each group."""
        processed: List[List[StatementParsedDTO]] = []
        for group in data:
            try:
                processed.append(self.transform_usecase.execute(group))
                self.logger.info(f"Processed group of {len(group)} statements")
            except Exception as exc:  # pragma: no cover - log and continue
                self.logger.error(f"Error processing group: {exc}")
        return processed

    def persist(
        self, data: List[List[StatementParsedDTO]]
    ) -> List[List[StatementParsedDTO]]:
        """Persist transformed statements to the repository."""
        for group in data:
            self.parsed_repo.save_all(group)
        return data

    def run(
        self, data: List[List[StatementParsedDTO]]
    ) -> List[List[StatementParsedDTO]]:
        """Run the transformation pipeline."""
        return super().run(data)
