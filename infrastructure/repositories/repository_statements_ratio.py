# infrastructure/repositories/repository_ratios.py
from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.statement_ratio_dto import StatementRatioDTO
from domain.ports.repository_statements_ratio_port import RepositoryStatementRatioPort 
from infrastructure.models.statements_Ratio_model import StatementRatioModel
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.utils.list_flatenner import ListFlattener


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
        flat_items = ListFlattener.flatten(items)
        valid_items = [i for i in flat_items if i is not None]
        for dto in valid_items:
            obj = model.from_dto(dto)
            data = {c.name: getattr(obj, c.name) for c in model.__table__.columns}
            stmt = insert(model).values(**data)
            update_dict = {
                c.name: getattr(stmt.excluded, c.name)
                for c in model.__table__.columns
                if c.name != "id"
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    "nsd",
                    "company_name",
                    "date",
                    "version",
                    "grupo",
                    "quadro",
                    "account",
                ],
                set_=update_dict,
            )
            session.execute(stmt)

    def get_by_company_name(self, company_name: str) -> list[StatementRatioDTO]:
        """Return Ratio statement rows for the given company."""
        with self.Session() as session:
            results = (
                session.query(StatementRatioModel)
                .filter(StatementRatioModel.company_name == company_name)
                .all()
            )
            return [r.to_dto() for r in results]

