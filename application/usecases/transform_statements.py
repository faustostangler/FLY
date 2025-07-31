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
        deduped = filter_latest_versions(raw_dtos)

        missing_map = validate_quarter_completeness(deduped)
        for key, miss in missing_map.items():
            self.logger.warning(
                "After dedupe, version-group %s missing quarters: %s",
                key,
                [d.strftime("%Y-%m-%d") for d in miss],
            )

        stage1 = self.math_transformer.transform(deduped)
        stage2 = self.intel_transformer.transform(stage1)  # type: ignore[arg-type]
        return stage2
