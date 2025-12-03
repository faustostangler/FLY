"""SQLite-backed repository implementation for company data."""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.dto.company_data_dto import CompanyDataDTO
from domain.ports import RepositoryCompanyDataPort, ConfigPort, LoggerPort
from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.models.company_data_model import CompanyDataModel
from infrastructure.repositories.sqlalchemy_repository_base import (
    SqlAlchemyRepositoryBase,
)


class SqlAlchemyRepositoryCompanyData(
    SqlAlchemyRepositoryBase[CompanyDataDTO, int],
    RepositoryCompanyDataPort,
):
    """SQLite/SQLAlchemy repository for ``CompanyDataDTO``.

    This adapter implements the RepositoryCompanyDataPort interface, providing
    persistence operations for company data via a local SQLite database.

    Note:
        Uses `check_same_thread=False` to support multithreading. Make sure session
        usage is isolated per thread to avoid concurrency issues.

        Write-Ahead Logging (WAL) mode is enabled to improve concurrent read/write behavior.
    """

    def __init__(
        self, connection_string: str, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize the SQLite-backed company repository."""
        super().__init__(connection_string, config, logger)

        self.config = config
        self.logger = logger

    # Provide a canonical factory the rest of infra can depend on.
    @property
    def session_factory(self):
        """Return the configured SQLAlchemy ``sessionmaker``."""
        # self.Session is the sessionmaker from SqlAlchemyEngineMixin
        return self.Session

    def save_all(self, items: List[CompanyDataDTO]) -> None:
        """Persist ``CompanyDataDTO`` objects using SQLite upserts."""
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
                    index_elements=["company_name"], set_=update_dict
                )
                session.execute(stmt)
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.log(f"Erro ao salvar CompanyDataDTO: {e}", level="debug")
            raise
        finally:
            session.close()

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return CompanyDataModel, (CompanyDataModel.id,)

    def get_cvm_by_name(self, company_name: str) -> str:
        """Lookup do código CVM a partir do nome da empresa."""
        session = self.Session()
        try:
            row = (
                session.query(CompanyDataModel.cvm_code)
                .filter(CompanyDataModel.company_name == company_name)
                .one_or_none()
            )
            if row is None:
                raise ValueError(f"Empresa não encontrada: {company_name}")
            return row[0]
        finally:
            session.close()
