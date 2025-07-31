"""Use case for transforming raw financial statement rows."""

from __future__ import annotations

from typing import List

from application.ports import StatementTransformerPort
from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.utils.validation_utils import validate_quarter_completeness
from domain.utils.version_utils import filter_latest_versions


class TransformStatementsUseCase:
    """Compose math and intel transformers into a single pipeline."""

    def __init__(
        self,
        math_transformer: StatementTransformerPort,
        intel_transformer: StatementTransformerPort,
    ) -> None:
        self.math_transformer = math_transformer
        self.intel_transformer = intel_transformer

    def execute(self, raw_dtos: List[RawStatementDTO]) -> List[ParsedStatementDTO]:
        """Run transformation pipeline for ``raw_dtos``."""
        # Stage 1: dedupe to latest version per quarter
        stage1 = filter_latest_versions(raw_dtos)

        from infrastructure.utils.csv_utils import save_dtos_to_csv

        save_dtos_to_csv(stage1, "raws_latest_statements.csv")

        # Stage 2: validate completeness
        missing_map = validate_quarter_completeness(stage1)
        if missing_map:
            for key, dates in missing_map.items():
                print(
                    f"After dedupe, group {key} missing quarters: "
                    f"{[d.strftime('%Y-%m-%d') for d in dates]}"
                )
        stage2_validated = stage1

        # Stage 3: math transformation
        stage3 = self.math_transformer.transform(stage2_validated)

        # Stage 4: intel transformation
        stage4 = self.intel_transformer.transform(stage3)  # type: ignore[arg-type]
        return stage4
