"""SQLAlchemy adapter for raw statement persistence."""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.dtos.raw_statement_dto import StatementRawDTO
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from infrastructure.utils.list_flatenner import ListFlattener
from infrastructure.models.raw_statements_model import StatementRawModel
from infrastructure.repositories.repository_base import RepositoryBase


class StatementRawRepository(
    RepositoryBase[StatementRawDTO, int],
    RepositoryStatementsRawPort,
):
    """SQLite-backed repository for ``StatementRawDTO`` objects."""

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
        return StatementRawModel, (StatementRawModel.id,)

    def save_all(self, items: List[StatementRawDTO]) -> None:
        """Persist raw statements using SQLite upserts."""
        session = self.Session()
        try:
            model, pk_columns = self.get_model_class()
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
                        "quarter",
                        "version",
                        "grupo",
                        "quadro",
                        "account",
                    ],
                    set_=update_dict,
                )
                session.execute(stmt)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_company_name(self, company_name: str) -> list[StatementRawDTO]:
        """Return raw statement rows for the given company."""
        with self.Session() as session:
            results = (
                session.query(StatementRawModel)
                .filter(StatementRawModel.company_name == company_name)
                .all()
            )
            return [r.to_dto() for r in results]
