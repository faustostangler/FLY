"""SQLAlchemy adapter for raw statement persistence."""

from __future__ import annotations

from typing import Tuple

from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import LoggerPort, SqlAlchemyRawStatementRepositoryPort
from infrastructure.config import Config
from infrastructure.models.raw_statement_model import RawStatementModel
from infrastructure.repositories.sqlalchemy_repository_base import (
    SqlAlchemyRepositoryBase,
)


class SqlAlchemyRawStatementRepository(
    SqlAlchemyRepositoryBase[RawStatementDTO, int],
    SqlAlchemyRawStatementRepositoryPort,
):
    """SQLite-backed repository for ``RawStatementDTO`` objects."""

    def __init__(self, config: Config, logger: LoggerPort) -> None:
        """Initialize repository with ``config`` and ``logger``."""
        super().__init__(config, logger)
        self.config = config
        self.logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return RawStatementModel, (RawStatementModel.id,)

    def get_by_company_name(self, company_name: str) -> list[RawStatementDTO]:
        """Return raw statement rows for the given company."""
        with self.Session() as session:
            results = (
                session.query(RawStatementModel)
                .filter(RawStatementModel.company_name == company_name)
                .all()
            )
            return [r.to_dto() for r in results]
