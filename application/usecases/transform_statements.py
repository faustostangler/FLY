"""Use case for transforming raw financial statement rows."""

from __future__ import annotations

from typing import List

from application.ports import StatementTransformerPort
from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import LoggerPort
from domain.utils.validation_utils import validate_quarter_completeness
from domain.utils.version_utils import filter_latest_versions


class TransformStatementsUseCase:
    """Compose math and intel transformers into a single pipeline."""

    def __init__(
        self,
        math_transformer: StatementTransformerPort,
        intel_transformer: StatementTransformerPort,
        logger: LoggerPort,
    ) -> None:
        """Store dependencies for the statement transformation pipeline."""
        self.math_transformer = math_transformer
        self.intel_transformer = intel_transformer
        self.logger = logger

    def execute(self, raw_dtos: List[RawStatementDTO]) -> List[ParsedStatementDTO]:
        """Run transformation pipeline for ``raw_dtos``."""
        missing = validate_quarter_completeness(raw_dtos)
        if missing:
            self.logger.log(
                f"Missing quarters in raw data: {[d.strftime('%Y-%m-%d') for d in missing]}",
                level="warning",
            )

        stage1 = filter_latest_versions(raw_dtos)
        stage2 = self.math_transformer.transform(stage1)
        stage3 = self.intel_transformer.transform(stage2)  # type: ignore[arg-type]
        return stage3
