"""SQLAlchemy adapter for parsed statement persistence."""

from __future__ import annotations

from dataclasses import replace
from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.dto import ParsedStatementDTO
from domain.ports import ConfigPort, LoggerPort, ParsedStatementRepositoryPort
from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.models.parsed_statement_model import ParsedStatementModel
from infrastructure.repositories.sqlalchemy_repository_base import (
    SqlAlchemyRepositoryBase,
)


class SqlAlchemyParsedStatementRepository(
    SqlAlchemyRepositoryBase[ParsedStatementDTO, int],
    ParsedStatementRepositoryPort,
):
    """SQLite-backed repository for ``ParsedStatementDTO`` objects."""

    def __init__(
        self, connection_string: str, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize repository with ``config`` and ``logger``."""
        super().__init__(connection_string, config, logger)

        self.config = config
        self.logger = logger

    def save_all(self, items: List[ParsedStatementDTO]) -> None:
        """Persist parsed statements using SQLite upserts."""
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
        return ParsedStatementModel, (ParsedStatementModel.id,)

    def exists_with_hash(self, company_name: str, hash_: str) -> bool:
        """Return True if ``company_name`` has rows with ``hash_``."""
        with self.Session() as session:
            query = session.query(ParsedStatementModel).filter(
                ParsedStatementModel.company_name == company_name,
                ParsedStatementModel.processing_hash == hash_,
            )
            return session.query(query.exists()).scalar()

    def replace_all_for_company(
        self,
        company_name: str,
        parsed_dtos: List[ParsedStatementDTO],
        new_hash: str,
    ) -> None:
        """Replace parsed rows for ``company_name`` with ``parsed_dtos``."""
        with self.Session() as session:
            session.query(ParsedStatementModel).filter(
                ParsedStatementModel.company_name == company_name
            ).delete()
            models = [
                ParsedStatementModel.from_dto(
                    replace(dto, processing_hash=new_hash, id=None)
                )
                for dto in parsed_dtos
            ]
            session.add_all(models)
            session.commit()
