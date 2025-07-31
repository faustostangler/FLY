import time
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Sequence, Tuple, TypeVar, Union

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from domain.ports import LoggerPort
from domain.ports.base_repository_port import SqlAlchemyRepositoryBasePort
from infrastructure.config import Config
from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.models.base_model import BaseModel

T = TypeVar("T")  # T any DTO.
K = TypeVar("K")  # Primary key type (e.g., str, int)


class SqlAlchemyRepositoryBase(SqlAlchemyRepositoryBasePort[T, K], ABC, Generic[T, K]):
    """
    Contract - Interface genérica para repositórios de leitura/escrita.
    Pode ser especializada para qualquer tipo de DTO.
    """

    def __init__(self, config: Config, logger: LoggerPort) -> None:
        """Initialize the repository infrastructure: engine, session, and schema.

        This constructor sets up the SQLite engine with threading support,
        configures the session factory for ORM transactions, and ensures
        that all declared models are created in the database.

        Args:
            config (Config): Application configuration containing the database connection string.
            logger (LoggerPort): Logger used for emitting repository lifecycle messages.
        """
        # Store configuration and logger for use throughout the repository
        self.config = config
        self.logger = logger

        # Create SQLAlchemy engine for SQLite with thread-safe settings
        self.engine = create_engine(
            config.database.connection_string,
            connect_args={
                "check_same_thread": False
            },  # allow usage from multiple threads
            future=True,
        )

        # Enable Write-Ahead Logging mode to support concurrent reads/writes
        with self.engine.connect() as conn:
            # conn.execute(text("PRAGMA optimize"))
            # conn.execute(text("PRAGMA synchronous=FULL"))
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.execute(text("PRAGMA cache_size=-65536"))  # 64 MB

        # Create a session factory for managing DB transactions
        self.Session = sessionmaker(
            bind=self.engine,
            autoflush=True,
            expire_on_commit=True,
        )

        # Automatically create all tables defined in the SQLAlchemy models
        BaseModel.metadata.create_all(self.engine)

        # self.logger.log(f"Create Instance Base Class {self.__class__.__name__}", level="info")

    @abstractmethod
    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy model class associated with the DTO.

        This method must be implemented by subclasses to specify which
        SQLAlchemy ORM model corresponds to the generic DTO type `T`.

        Returns:
            type: The SQLAlchemy ORM model class.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        # Must be implemented by subclass to define the ORM mapping
        raise NotImplementedError

    def save_all(self, items: List[T]) -> None:
        """Persist a list of DTOs in bulk.

        Args:
            items (List[T]): A list (possibly nested) of DTOs to be persisted.
        """
        # Create a new SQLAlchemy session
        session = self.Session()

        # Retrieve the SQLAlchemy model class associated with the DTO type
        model, pk_columns = self.get_model_class()

        try:
            # Flatten nested lists into a single-level list of DTOs
            flat_items = ListFlattener.flatten(items)

            # Remove any None values from the list
            valid_items = [item for item in flat_items if item is not None]

            # Merge each DTO into the current session (insert or update)
            for dto in valid_items:
                session.merge(model.from_dto(dto))

            # Commit the transaction to persist all changes
            session.commit()

            # Log the number of successfully saved items
            if len(valid_items) > 0:
                self.logger.log(
                    f"Saved {len(valid_items)} items",
                    level="info",
                )
        except Exception as e:
            # Roll back the transaction in case of error
            session.rollback()

            # Log the failure reason
            self.logger.log(
                f"Failed to save items: {e}",
                level="error",
            )

            # Re-raise the exception to propagate the error
            raise
        finally:
            # Ensure the session is always closed after execution
            session.close()

    def get_all_old(self) -> List[T]:
        """Retrieve all persisted DTOs from the database.

        This method loads all records from the table corresponding to the DTO's
        associated ORM model and converts them into DTO instances.

        Returns:
            List[T]: A list of DTOs retrieved from the database.
        """
        # Create a new SQLAlchemy session
        session = self.Session()

        # Get the SQLAlchemy model class linked to the current DTO type
        model, pk_columns = self.get_model_class()

        try:
            # Query all rows from the corresponding table
            results = session.query(model).order_by(*pk_columns).all()

            # Sort py PK
            results.sort(key=lambda obj: self._sort_key(obj, pk_columns))

            # Convert each ORM instance into a DTO
            return [model.to_dto() for model in results]
        finally:
            # Ensure the session is closed even if an error occurs
            session.close()

    def get_all(self, batch_size: int = 100) -> List[T]:
        """
        Retrieve all DTOs from the database using paginated cursor-based fetching.

        This method fetches all records incrementally using the 'id' field to
        avoid loading the entire dataset into memory at once.

        Args:
            batch_size (int): Number of rows to fetch per query.

        Returns:
            List[T]: A list of all DTOs retrieved from the database.
        """
        batch_size = batch_size or self.config.global_settings.batch_size

        # Create a new SQLAlchemy session
        session = self.Session()

        # Get the SQLAlchemy model class linked to the current DTO type
        model, pk_columns = self.get_model_class()

        all_results: List[T] = []
        last_id = 0

        while True:
            batch = (
                session.query(model)
                .filter(model.id > last_id)
                .order_by(model.id)
                .limit(batch_size)
                .all()
            )

            if not batch:
                break

            all_results.extend([m.to_dto() for m in batch])
            last_id = batch[-1].id
        return all_results

    def get_all_primary_keys(self) -> List[K]:
        """Retrieve all unique primary keys from the database.

        This method queries the repository for all distinct identifiers
        (e.g., CVM codes) of the persisted records.

        Returns:
            Set[str]: A set containing all unique primary keys currently stored.
        """
        # Create a new SQLAlchemy session
        session = self.Session()

        # Get the SQLAlchemy model class linked to the current DTO type
        model, pk_columns = self.get_model_class()

        try:
            # Execute a distinct query for the primary key column
            results = session.query(*pk_columns).distinct().order_by(*pk_columns).all()

            # Sort py PK
            results.sort(key=lambda obj: self._sort_key(obj, pk_columns))

            # Extract and collect non-null keys into a set
            return [row[0] for row in results if row[0]]

        finally:
            # Ensure session is always closed
            session.close()

    def get_existing_by_columns(
        self, column_names: Union[str, List[str]]
    ) -> List[Tuple]:
        """Return distinct and ordered values for one or more given columns.

        Examples:
            repo.get_existing_by_columns("nsd") -> [("94790",), ("12345",)]
            repo.get_existing_by_columns(["nsd", "company_name"]) -> [("94790", "ACME"), ("12345", "ROMI")]

        Args:
            column_names: A single column name as string, or a list of column names.

        Returns:
            A list of tuples with distinct and ordered values.
        """
        session = self.Session()

        # Retrieve the SQLAlchemy model class associated with the DTO type
        model, pk_columns = self.get_model_class()

        try:
            if isinstance(column_names, str):
                column_names = [column_names]

            kw_columns = [getattr(model, name) for name in column_names]
            rows = session.query(*kw_columns).distinct().all()

            # remove nulls
            results = [row for row in rows if not any(field is None for field in row)]

            # Create a lightweight wrapper to simulate attribute access on a tuple
            class RowWrapper:
                def __init__(self, values):
                    # Store the original tuple of values
                    self._values = values

                def __getattr__(self, key):
                    # Find the index of the requested column name
                    idx = column_names.index(key)
                    # Return the value at that index in the tuple
                    return self._values[idx]

            # Sort the result list using a custom sort key
            results.sort(
                key=lambda row:
                # Wrap the tuple to enable attribute-style access
                self._sort_key(RowWrapper(row), kw_columns)
            )

            return results
        finally:
            session.close()

    def has_item(self, identifier: K) -> bool:
        """Check if a record with the given identifier exists in the database.

        This method queries the repository by primary key (e.g., CVM code)
        to determine if a matching entry is already persisted.

        Args:
            identifier (str): The unique identifier (e.g., CVM code) to check for existence.

        Returns:
            bool: True if the record exists, False otherwise.
        """
        # Create a new SQLAlchemy session
        session = self.Session()

        # Get the SQLAlchemy model class linked to the current DTO type
        model, pk_columns = self.get_model_class()

        try:
            if len(pk_columns) == 1:
                filter_expr = pk_columns[0] == identifier
            else:
                assert isinstance(identifier, tuple), "Expected tuple for composite key"
                filter_expr = [col == val for col, val in zip(pk_columns, identifier)]
            # Perform a filtered query and check if any result is found
            query = (
                session.query(model).filter(*filter_expr)
                if isinstance(filter_expr, list)
                else session.query(model).filter(filter_expr)
            )

            return query.first() is not None
        finally:
            # Always close the session after the query
            session.close()

    def get_by_id(self, identifier: K) -> T:
        """Retrieve a DTO by its unique identifier (e.g., CVM code).

        This method performs a lookup in the database using the primary key
        and returns the corresponding DTO. Raises an error if not found.

        Args:
            id (str): The unique identifier (e.g., CVM code) of the entity to retrieve.

        Returns:
            T: The DTO object associated with the given identifier.

        Raises:
            ValueError: If no record is found with the specified ID.
        """
        # Create a new SQLAlchemy session
        session = self.Session()

        # Get the SQLAlchemy model class linked to the current DTO type
        model, pk_columns = self.get_model_class()

        try:
            if len(pk_columns) == 1:
                filter_expr = pk_columns[0] == identifier
            else:
                assert isinstance(identifier, tuple), "Expected tuple for composite key"
                filter_expr = [col == val for col, val in zip(pk_columns, identifier)]

            query = (
                session.query(model).filter(*filter_expr)
                if isinstance(filter_expr, list)
                else session.query(model).filter(filter_expr)
            )
            obj = query.first()

            if not obj:
                raise ValueError(f"Data not found: {identifier}")

            return obj.to_dto()
        finally:
            # Ensure the session is closed in all cases
            session.close()

    def get_page_after(self, last_id: int, limit: int) -> List[T]:
        """Return a page of DTOs ordered by surrogate id."""
        session = self.Session()
        model, _ = self.get_model_class()
        try:
            query = (
                session.query(model)
                .filter(model.id > last_id)
                .order_by(model.id)
                .limit(limit)
            )
            return [obj.to_dto() for obj in query.all()]
        finally:
            session.close()

    def _safe_cast(self, value: Any) -> Union[int, str]:
        try:
            return int(value)
        except (ValueError, TypeError):
            return str(value)

    def _sort_key(self, obj: Any, pk_columns: Sequence) -> tuple[Union[int, str], ...]:
        return tuple(self._safe_cast(getattr(obj, col.key)) for col in pk_columns)
