"""Use case for transforming raw financial statement rows."""

from __future__ import annotations

from typing import List

from domain.dto.statement_fetched_dto import StatementFetchedDTO
from domain.ports import ConfigPort, LoggerPort, StatementTransformerPort
from domain.utils.validation_utils import validate_quarter_completeness
from domain.utils.version_utils import filter_latest_versions


class TransformStatementsUseCase:
    """Compose math and intel transformers into a single pipeline."""

    def __init__(
        self,
        math_transformer: StatementTransformerPort,
        intel_transformer: StatementTransformerPort,
        config: ConfigPort,
        logger: LoggerPort,
    ) -> None:
        self.math_transformer = math_transformer
        self.intel_transformer = intel_transformer
        self.config = config
        self.logger = logger

    def execute(
        self, fetched_dtos: List[StatementFetchedDTO]
    ) -> List[StatementFetchedDTO]:
        """Run transformation pipeline for ``fetched_dtos``."""
        stage1 = filter_latest_versions(fetched_dtos)

        from infrastructure.utils.csv_utils import save_dtos_to_csv

        save_dtos_to_csv(stage1, "raws_statements_stage_1.csv")

        # Stage 1.5: restrict validation to MATH_TARGET_ACCOUNTS
        targets = tuple(self.config.transformers.math_target_accounts)
        validation_candidates = [r for r in stage1 if r.account in targets]

        # Stage 2: detect missing quarter-ends only for filtered accounts
        missing_map = validate_quarter_completeness(validation_candidates)
        if missing_map:
            for key, dates in missing_map.items():
                self.logger.warning(
                    f"After dedupe, account-group {key} missing quarters: {[d.strftime('%Y-%m-%d') for d in dates]}"
                )
        stage2 = stage1  # in fact impplement raw_statement download by nsd search for missing then proceed to stage2

        from infrastructure.utils.csv_utils import save_dtos_to_csv

        save_dtos_to_csv(stage2, "raws_statements_stage_2.csv")

        # Stage 3: math transformation
        stage3 = self.math_transformer.transform(stage2)

        from infrastructure.utils.csv_utils import save_dtos_to_csv

        save_dtos_to_csv(stage3, "raws_statements_stage_3.csv")

        # Stage 4: intel transformation
        stage4 = self.intel_transformer.transform(stage3)  # type: ignore[arg-type]

        from infrastructure.utils.csv_utils import save_dtos_to_csv

        save_dtos_to_csv(stage4, "raws_statements_stage_4.csv")

        return stage4
