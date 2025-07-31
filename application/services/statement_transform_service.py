"""Service to batch-transform raw statements into parsed rows."""

from __future__ import annotations

from typing import List

from application.usecases.transform_statements import TransformStatementsUseCase
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import (
    LoggerPort,
    SqlAlchemyParsedStatementRepositoryPort,
    SqlAlchemyRawStatementRepositoryPort,
)
from domain.utils import compute_hash
from infrastructure.config import Config
from infrastructure.transformers import (
    IntelStatementTransformerAdapter,
    MathStatementTransformerAdapter,
)


class StatementTransformService:
    """Transform raw statement rows in company batches."""

    def __init__(
        self,
        config: Config,
        logger: LoggerPort,
        raw_repo: SqlAlchemyRawStatementRepositoryPort,
        parsed_repo: SqlAlchemyParsedStatementRepositoryPort,
    ) -> None:
        """Create service with repositories and configuration."""
        self.logger = logger
        self.raw_repo = raw_repo
        self.parsed_repo = parsed_repo

        math_transformer = MathStatementTransformerAdapter(config)
        intel_transformer = IntelStatementTransformerAdapter(config)
        self.transform_usecase = TransformStatementsUseCase(
            math_transformer=math_transformer,
            intel_transformer=intel_transformer,
        )

    def transform_all(self) -> None:
        """Process raw rows one company at a time."""
        company_keys = self.raw_repo.get_existing_by_columns("company_name")

        for (company_name,) in company_keys:
            raw_dtos: List[RawStatementDTO] = self.raw_repo.get_by_company_name(
                company_name
            )

            current_hash = compute_hash(raw_dtos)

            if self.parsed_repo.exists_with_hash(company_name, current_hash):
                self.logger.log(f"[{company_name}] - Already processed. Skipping.")
                continue

            self.logger.log(f"[{company_name}] - Processing.")

            try:
                parsed_dtos = self.transform_usecase.execute(raw_dtos)
                self.parsed_repo.replace_all_for_company(
                    company_name, parsed_dtos, current_hash
                )
                self.logger.log(
                    f"[{company_name}] Transformation completed.", level="info"
                )
            except Exception as exc:  # pragma: no cover - log and continue
                self.logger.log(f"[{company_name}] Error: {exc}", level="error")

