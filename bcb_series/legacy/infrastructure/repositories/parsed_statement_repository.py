"""SQLAlchemy adapter for fetched statement persistence."""

from __future__ import annotations

from dataclasses import replace
from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.dto import StatementFetchedDTO
from domain.ports import ConfigPort, LoggerPort, RepositoryStatementFetchedPort
from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.models.fetched_statement_model import StatementFetchedModel
from infrastructure.repositories.sqlalchemy_repository_base import (
    SqlAlchemyRepositoryBase,
)


class SqlAlchemyStatementFetchedRepository(
    SqlAlchemyRepositoryBase[StatementFetchedDTO, int],
    RepositoryStatementFetchedPort,
):
    """SQLite-backed repository for ``StatementFetchedDTO`` objects."""

    def __init__(
        self, connection_string: str, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize repository with ``config`` and ``logger``."""
        super().__init__(connection_string, config, logger)

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

    def exists_with_hash(self, company_name: str, hash_: str) -> bool:
        """Return True if ``company_name`` has rows with ``hash_``."""
        with self.Session() as session:
            query = session.query(StatementFetchedModel).filter(
                StatementFetchedModel.company_name == company_name,
                StatementFetchedModel.processing_hash == hash_,
            )
            return session.query(query.exists()).scalar()

    def replace_all_for_company(
        self,
        company_name: str,
        fetched_dtos: List[StatementFetchedDTO],
        new_hash: str,
    ) -> None:
        """Replace fetched rows for ``company_name`` with ``fetched_dtos``."""
        with self.Session() as session:
            session.query(StatementFetchedModel).filter(
                StatementFetchedModel.company_name == company_name
            ).delete()
            models = [
                StatementFetchedModel.from_dto(
                    replace(dto, processing_hash=new_hash, id=None)
                )
                for dto in fetched_dtos
            ]
            session.add_all(models)
            session.commit()
