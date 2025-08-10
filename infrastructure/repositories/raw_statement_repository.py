"""SQLAlchemy adapter for raw statement persistence."""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.ports import ConfigPort
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import LoggerPort, SqlAlchemyRawStatementRepositoryPort
from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.models.raw_statement_model import RawStatementModel
from infrastructure.repositories.sqlalchemy_repository_base import (
    SqlAlchemyRepositoryBase,
)


class SqlAlchemyRawStatementRepository(
    SqlAlchemyRepositoryBase[RawStatementDTO, int],
    SqlAlchemyRawStatementRepositoryPort,
):
    """SQLite-backed repository for ``RawStatementDTO`` objects."""

    def __init__(
        self, database_url: str, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize repository with ``config`` and ``logger``."""
        super().__init__(database_url, config, logger)
        self.config = config
        self.logger = logger

    def save_all(self, items: List[RawStatementDTO]) -> None:
        """Persist raw statements using SQLite upserts."""
        session = self.Session()
        try:
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
