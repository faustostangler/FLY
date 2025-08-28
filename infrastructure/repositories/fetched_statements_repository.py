"""SQLAlchemy adapter for fetched statement persistence."""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.dtos.fetched_statement_dto import StatementFetchedDTO
from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from infrastructure.utils.list_flatenner import ListFlattener
from infrastructure.models.fetched_statements_model import StatementFetchedModel
from infrastructure.repositories.base_repository import RepositoryBase


class StatementFetchedRepository(
    RepositoryBase[StatementFetchedDTO, int],
    RepositoryStatementFetchedPort,
):
    """SQLite-backed repository for ``StatementFetchedDTO`` objects."""

    def __init__(
        self, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize repository with ``config`` and ``logger``."""
        super().__init__(config, logger)
        self.config = config
        self.logger = logger

    def save_all(self, items: List[StatementFetchedDTO]) -> None:
        """Persist fetched statements using SQLite upserts."""
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

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return StatementFetchedModel, (StatementFetchedModel.id,)

    def get_by_company_name(self, company_name: str) -> list[StatementFetchedDTO]:
        """Return fetched statement rows for the given company."""
        with self.Session() as session:
            results = (
                session.query(StatementFetchedModel)
                .filter(StatementFetchedModel.company_name == company_name)
                .all()
            )
            return [r.to_dto() for r in results]
