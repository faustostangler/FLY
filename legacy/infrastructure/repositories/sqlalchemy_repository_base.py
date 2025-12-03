from abc import ABC, abstractmethod
from typing import (
    Any,
    Generator,
    Generic,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)
from itertools import product
from sqlalchemy import tuple_ as sa_tuple
from domain.ports import ConfigPort, LoggerPort
from domain.ports.repository_base_port import RepositoryBasePort
from infrastructure.adapters.sqlalchemy_engine_mixin import SqlAlchemyEngineMixin
from infrastructure.helpers.list_flattener import ListFlattener

T = TypeVar("T")  # T any DTO.
K = TypeVar("K")  # Primary key type (e.g., str, int)


class SqlAlchemyRepositoryBase(
    RepositoryBasePort[T, K], SqlAlchemyEngineMixin, ABC, Generic[T, K]
):
    """
    Contract - Interface genérica para repositórios de leitura/escrita.
    Pode ser especializada para qualquer tipo de DTO.
    """

    def __init__(
        self, connection_string: str, config: ConfigPort, logger: LoggerPort
    ) -> None:
        self.config = config
        super().__init__(connection_string, logger)

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

    def save_all(self, items: Sequence[T]) -> None:
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

    # def get_all_old(self) -> List[T]:
    #     """Retrieve all persisted DTOs from the database.

    #     This method loads all records from the table corresponding to the DTO's
    #     associated ORM model and converts them into DTO instances.

    #     Returns:
    #         List[T]: A list of DTOs retrieved from the database.
    #     """
    #     # Create a new SQLAlchemy session
    #     session = self.Session()

    #     # Get the SQLAlchemy model class linked to the current DTO type
    #     model, pk_columns = self.get_model_class()

    #     try:
    #         # Query all rows from the corresponding table
    #         results = session.query(model).order_by(*pk_columns).all()

    #         # Sort py PK
    #         results.sort(key=lambda obj: self._sort_key(obj, pk_columns))

    #         # Convert each ORM instance into a DTO
    #         return [model.to_dto() for model in results]
    #     finally:
    #         # Ensure the session is closed even if an error occurs
    #         session.close()

    def get_all(self, batch_size: int = 100) -> List[T]:
        """Retrieve all DTOs from the database using paginated cursor-based
        fetching.

        This method fetches all records incrementally using the 'id' field to
        avoid loading the entire dataset into memory at once.

        Args:
            batch_size (int): Number of rows to fetch per query.

        Returns:
            List[T]: A list of all DTOs retrieved from the database.
        """
        # batch_size = batch_size or self.config.global_settings.batch_size

        # # Create a new SQLAlchemy session
        # session = self.Session()

        # # Get the SQLAlchemy model class linked to the current DTO type
        # model, pk_columns = self.get_model_class()

        # all_results: List[T] = []
        # last_id = 0

        # while True:
        #     batch = (
        #         session.query(model)
        #         .filter(model.id > last_id)
        #         .order_by(model.id)
        #         .limit(batch_size)
        #         .all()
        #     )

        #     if not batch:
        #         break

        #     all_results.extend([m.to_dto() for m in batch])
        #     last_id = batch[-1].id
        # return all_results
        batch_size = batch_size or self.config.global_settings.batch_size
        model, pk_columns = self.get_model_class()
        all_results: List[T] = []
        last_key: Optional[Union[int, str]] = None

        session = self.Session()
        try:
            while True:
                # assume PK único; se for composto pode usar pk_columns tuple
                col = pk_columns[0]
                q = session.query(model)
                if last_key is not None:
                    q = q.filter(col > last_key)
                batch = q.order_by(col).limit(batch_size).all()
                if not batch:
                    break
                all_results.extend(m.to_dto() for m in batch)
                last_key = getattr(batch[-1], col.key)
            return all_results
        finally:
            session.close()

    def iter_all(self, batch_size: int | None = None) -> Generator[T, None, None]:
        """Yield all DTOs sequentially using keyset pagination over the PK."""
        size = batch_size or self.config.global_settings.batch_size
        model, pk_columns = self.get_model_class()
        # self.logger.log(
        #     f"iter_all start batch_size={size}",
        #     level="info",
        # )
        yielded = 0
        try:
            if len(pk_columns) == 1:
                gen = self._iter_all_simple(size)
            else:
                gen = self._iter_all_composite(size)
            for dto in gen:
                yielded += 1
                yield dto
        finally:
            pass
            # self.logger.log(
            #     f"iter_all finished total={yielded}",
            #     level="info",
            # )

    def _iter_all_simple(self, size: int) -> Generator[T, None, None]:
        model, pk_columns = self.get_model_class()
        col = pk_columns[0]
        last_key: Optional[Any] = None
        with self.Session() as session:
            base_q = (
                session.query(model)
                .order_by(col)
                .yield_per(size)
                .execution_options(stream_results=True)
                .enable_eagerloads(False)
            )
            while True:
                q = base_q
                if last_key is not None:
                    q = q.filter(col > last_key)
                count = 0
                for m in q.limit(size):
                    yield m.to_dto()
                    last_key = getattr(m, col.key)
                    count += 1
                if count == 0:
                    break

    def _iter_all_composite(self, size: int) -> Generator[T, None, None]:
        model, pk_columns = self.get_model_class()
        last_key: Optional[Tuple] = None
        with self.Session() as session:
            base_q = (
                session.query(model)
                .order_by(*pk_columns)
                .yield_per(size)
                .execution_options(stream_results=True)
                .enable_eagerloads(False)
            )
            while True:
                q = base_q
                if last_key is not None:
                    q = q.filter(sa_tuple(*pk_columns) > sa_tuple(*last_key))
                count = 0
                for m in q.limit(size):
                    yield m.to_dto()
                    last_key = tuple(getattr(m, c.key) for c in pk_columns)
                    count += 1
                if count == 0:
                    break

    def get_all_primary_keys(self) -> List[str]:
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

    def iter_existing_by_columns(
        self,
        column_names: Union[str, List[str]],
        *,
        batch_size: int | None = None,
        include_nulls: bool = False,
    ) -> Iterator[Tuple]:
        """Stream distinct column values in deterministic order.

        Chunked iteration relies on SQLAlchemy's ``yield_per`` to limit rows
        loaded into memory. ``stream_results=True`` is retained for
        compatibility but does not enable server-side cursors on SQLite.
        """
        size = batch_size or self.config.global_settings.batch_size
        model, _ = self.get_model_class()
        if isinstance(column_names, str):
            column_names = [column_names]
        columns = [getattr(model, col) for col in column_names]

        with self.Session() as session:
            query = session.query(*columns).distinct().order_by(*columns)
            if not include_nulls:
                for col in columns:
                    query = query.filter(col.isnot(None))
            query = (
                query.yield_per(size)
                .execution_options(stream_results=True)
                .enable_eagerloads(False)
            )
            for row in query:
                yield tuple(row)

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

    def get_by_column_values(
        self,
        column_names: Union[str, List[str]],
        values: Union[Any, List[Any]],
    ) -> List[T]:
        """
        Filtra registros com múltiplas colunas. Se o valor de alguma coluna for vazio (None, '', []),
        ela será ignorada do filtro — equivalente a "qualquer valor".

        - Para 1 coluna: filtro simples com .in_()
        - Para várias colunas: gera produto cartesiano das colunas ativas
        - Colunas com filtro vazio são removidas da condição

        Exemplo:
            get_by_column_values(
                ["company_name", "nsd_type"],
                [["ACME", "ROMI"], ""]
            ) ⇒ WHERE company_name IN ('ACME', 'ROMI')
        """
        session = self.Session()
        model, _ = self.get_model_class()

        try:
            if isinstance(column_names, str):
                column_names = [column_names]
                
            if not isinstance(values, list):
                values = [values]

            # 👇 ajuste: se só tem 1 coluna e a lista não é uma lista de listas, encapsula
            if len(column_names) == 1 and (not any(isinstance(v, list) for v in values)):
                values = [values]

            # Normaliza: sempre listas
            normalized_values = []
            active_columns = []
            for col, val in zip(column_names, values):
                if isinstance(val, list):
                    clean = [v for v in val if v not in (None, '')]
                else:
                    clean = [val] if val not in (None, '') else []

                if clean:
                    active_columns.append(col)
                    normalized_values.append(clean)

            if not active_columns:
                # nenhum filtro => retorna tudo
                return [obj.to_dto() for obj in session.query(model).all()]

            if len(active_columns) == 1:
                col = getattr(model, active_columns[0])
                query_filter = col.in_(normalized_values[0])
            else:
                cols = [getattr(model, c) for c in active_columns]
                combinations = list(product(*normalized_values))
                if not combinations:
                    return []
                query_filter = sa_tuple(*cols).in_(combinations)

            results = session.query(model).filter(query_filter).all()
            return [obj.to_dto() for obj in results]

        finally:
            session.close()

    def get_page_after(self, last_id: int, limit: int) -> List[T]:
        """Return a page of DTOs ordered by surrogate id."""
        session = self.Session()
        model, pk_columns = self.get_model_class()
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
