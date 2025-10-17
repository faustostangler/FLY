# infrastructure/repositories/repository_ratios.py
from __future__ import annotations

from typing import List, Tuple

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.statement_ratio_dto import StatementRatioDTO
from domain.ports.repository_statements_ratio_port import RepositoryStatementRatioPort 
from infrastructure.models.statements_ratio_model import StatementRatioModel
from infrastructure.repositories._shared import (
    execute_sqlite_upsert,
    iter_valid_dtos,
)
from infrastructure.repositories.repository_base import RepositoryBase


class StatementRatioRepository(
    RepositoryBase[StatementRatioDTO, int],
    RepositoryStatementRatioPort,
):
    """SQLite-backed repository for ``StatementRatioDTO`` objects."""

    def __init__(
        self, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize repository with ``config`` and ``logger``."""
        super().__init__(config, logger)
        self.config = config
        self.logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return StatementRatioModel, (StatementRatioModel.id,)

    def save_all(self, items: List[StatementRatioDTO], *, uow: Uow) -> None:
        """Persist Ratio statements using SQLite upserts."""

        session = uow.session
        model, _ = self.get_model_class()

        valid_items = list(iter_valid_dtos(items))
        if not valid_items:
            return

        for dto in valid_items:
            execute_sqlite_upsert(
                session,
                model,
                dto,
                conflict_columns=(
                    "nsd",
                    "company_name",
                    "date",
                    "version",
                    "grupo",
                    "quadro",
                    "account",
                ),
                skip_update_columns=("id",),
            )

    def get_by_company_name(
        self, company_name: str, *, uow: Uow
    ) -> list[StatementRatioDTO]:
        """Return Ratio statement rows for the given company."""

        session = uow.session
        results = (
            session.query(StatementRatioModel)
            .filter(StatementRatioModel.company_name == company_name)
            .all()
        )
        return [r.to_dto() for r in results]

