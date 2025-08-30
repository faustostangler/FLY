from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.dtos.company_data_dto import CompanyDataDTO
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from infrastructure.models.company_data_model import CompanyDataModel
from infrastructure.repositories.base_repository import RepositoryBase

# from infrastructure.uils.list_flattener import ListFlattener


class RepositoryCompanyData(
    RepositoryBase[CompanyDataDTO, int],
    RepositoryCompanyDataPort):
    """SQLite/SQLAlchemy repository for company data.

    Implements the `RepositoryCompanyDataPort` using a local SQLite database
    with SQLAlchemy Core/ORM.

    Notes:
        - Uses `check_same_thread=False` in the engine (configured upstream) to enable
          multi-threaded access. Sessions must not be shared across threads.
        - Enables Write-Ahead Logging (WAL) at the engine level to improve concurrent
          read/write behavior.

    Args:
        config (ConfigPort): Configuration provider used by the base repository.
        logger (LoggerPort): Logger provider used for diagnostics.

    """

    def __init__(
        self, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize the repository with configuration and logger.

        Args:
            config (ConfigPort): Application configuration port.
            logger (LoggerPort): Application logger port.
        """
        # Initialize base repository infrastructure (engine, Session, etc.)
        super().__init__(config, logger)

        # Keep references for convenience inside repository methods
        self.config = config
        self.logger = logger

    # Provide a canonical factory the rest of infra can depend on.
    @property
    def session_factory(self):
        """Return the configured SQLAlchemy session factory.

        Returns:
            Any: The `sessionmaker` instance created by the base repository.
        """
        # `self.Session` is provided by `SqlAlchemyEngineMixin` in the base class
        return self.Session

    def save_all(self, items: List[CompanyDataDTO]) -> None:
        """Upsert all provided `CompanyDataDTO` items into SQLite.

        Performs batched upserts using `INSERT ... ON CONFLICT DO UPDATE` keyed on
        `company_name`. Commits once at the end for consistency.

        Args:
            items (List[CompanyDataDTO]): Collection of DTOs to persist.

        Raises:
            Exception: Propagates any database or data-mapping errors after logging.

        Notes:
            - This method expects a `ListFlattener.flatten` utility. If it is not
              available/imported, a `NameError` will occur. Ensure the import
              `from infrastructure.uils.list_flattener import ListFlattener`
              is enabled or provide an equivalent flattener.
        """
        # Create a short-lived session for this unit of work
        session = self.Session()
        try:
            # Resolve ORM model and primary key columns
            model, pk_columns = self.get_model_class()

            # Normalize potentially nested inputs into a flat list
            flat_items = items # ListFlattener.flatten(items)

            # Filter out `None` values to avoid mapping errors
            valid_items = [i for i in flat_items if i is not None]

            # Upsert each DTO using a deterministic conflict target
            for dto in valid_items:
                # Convert DTO into ORM instance
                obj = model.from_dto(dto)

                # Build a plain dict for SQLAlchemy Core insert
                data = {c.name: getattr(obj, c.name) for c in model.__table__.columns}

                # Prepare an INSERT statement with all fields
                stmt = insert(model).values(**data)

                # Define update payload excluding the PK
                update_dict = {
                    c.name: getattr(stmt.excluded, c.name)
                    for c in model.__table__.columns
                    if c.name != "id"
                }

                # Apply ON CONFLICT DO UPDATE on a unique business key
                stmt = stmt.on_conflict_do_update(
                    index_elements=["company_name"], set_=update_dict
                )

                # Execute the upsert operation
                session.execute(stmt)

            # Commit the transaction once after processing all items
            session.commit()
        except Exception as e:
            # Roll back the transaction on any failure to maintain atomicity
            session.rollback()

            # Log the error at debug level with contextual information
            self.logger.log(f"Erro ao salvar CompanyDataDTO: {e}", level="debug")
            raise
        finally:
            # Ensure session resources are always released
            session.close()

        # Intentionally disabled noisy lifecycle log; re-enable if needed.
        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the ORM model class and primary key tuple used by this repository.

        Returns:
            Tuple[type, tuple]: A tuple of (model class, primary key columns).
        """
        # Provide the bound model and its primary key columns
        return CompanyDataModel, (CompanyDataModel.id,)

    def get_cvm_by_name(self, company_name: str) -> str:
        """Look up the CVM code for a company by its name.

        Args:
            company_name (str): Exact company name to search.

        Returns:
            str: The CVM code associated with the company.

        Raises:
            ValueError: If the company name is not found.
        """
        # Create a short-lived session for this query
        session = self.Session()
        try:
            # Query only the needed column for efficiency
            row = (
                session.query(CompanyDataModel.cvm_code)
                .filter(CompanyDataModel.company_name == company_name)
                .one_or_none()
            )

            # Validate presence and return the scalar value
            if row is None:
                raise ValueError(f"Empresa não encontrada: {company_name}")
            return row[0]
        finally:
            # Ensure session resources are always released
            session.close()
