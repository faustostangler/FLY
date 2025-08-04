"""SQLite-backed repository implementation for company data."""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.dto.company_data_dto import CompanyDataDTO
from domain.ports import LoggerPort, SqlAlchemyCompanyDataRepositoryPort
from infrastructure.config import Config
from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.models.company_data_model import CompanyDataModel
from infrastructure.repositories.sqlalchemy_repository_base import (
    SqlAlchemyRepositoryBase,
)


class SqlAlchemyCompanyDataRepository(
    SqlAlchemyRepositoryBase[CompanyDataDTO, int],
    SqlAlchemyCompanyDataRepositoryPort,
):
    """Concrete repository implementation for CompanyDataDTO using SQLite and
    SQLAlchemy.

    This adapter implements the CompanyDataRepositoryPort interface, providing persistence
    operations for company data via a local SQLite database.

    Note:
        Uses `check_same_thread=False` to support multithreading. Make sure session
        usage is isolated per thread to avoid concurrency issues.

        Write-Ahead Logging (WAL) mode is enabled to improve concurrent read/write behavior.
    """

    def __init__(self, config: Config, logger: LoggerPort) -> None:
        """Initialize the SQLite-backed company repository.

        Args:
            config (Config): Application configuration with database connection details.
            logger (LoggerPort): Logging adapter used for tracking internal behavior.
        """
        super().__init__(config, logger)

        self.config = config
        self.logger = logger

    def save_all(self, items: List[CompanyDataDTO]) -> None:
        """Persist ``CompanyDataDTO`` objects using SQLite upserts."""
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
                    index_elements=["cvm_code"], set_=update_dict
                )
                session.execute(stmt)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return CompanyDataModel, (CompanyDataModel.cvm_code,)
