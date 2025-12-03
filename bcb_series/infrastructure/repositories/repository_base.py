from __future__ import annotations

from typing import (
    Any,
    Generic,
    Iterable,
    Iterator,
    List,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

from sqlalchemy import and_, or_, select
from sqlalchemy.engine import Row

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.ports.repository_base_port import RepositoryBasePort
from infrastructure.adapters.engine_setup import EngineSetup

# from infrastructure.utils.list_flattener import ListFlattener

T = TypeVar("T")  # T any DTO.
K = TypeVar("K", covariant=True)  # Primary key type (e.g., str, int)


class RepositoryBase(EngineSetup, RepositoryBasePort[T, K]):
    """Generic read/write repository contract with keyset-based helpers.

    This class provides common persistence utilities for repositories that map
    DTOs (type ``T``) to SQLAlchemy ORM models, including bulk saves, keyset
    pagination, existence checks, and filtered queries. It must be specialized
    by concrete repositories that implement the ORM mapping via
    :meth:`get_model_class`.

    The repository depends on:
      * ``EngineSetup``: provides SQLAlchemy engine/session management.
      * ``RepositoryBasePort``: defines the high-level repository interface.
      * ``ConfigPort``: carries database URI and repository defaults.
      * ``LoggerPort``: structured logging for operations and failures.
    """

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        # Initialize SQLAlchemy engine/session using the configured connection string
        super().__init__(config.database.connection_string, logger)

        # Keep references to ports for later use
        self.config = config
        self.logger = logger

    def save_all(self, items: List[T], *, uow: Uow) -> None:
        """Persist a list (possibly nested) of DTOs in a single transaction.

        Merges each DTO into the session (upsert semantics via SQLAlchemy
        ``merge``). Any ``None`` values in the input are ignored.

        Args:
            items (List[T]): A list (potentially nested) of DTOs to persist.

        Notes:
            This method expects a ``ListFlattener.flatten`` utility to be
            available for nested-list normalization. The import is currently
            commented out; ensure it is provided by the concrete project setup.
        """
        # Create a new SQLAlchemy session
        session = uow.session

        # Retrieve the SQLAlchemy model class associated with the DTO type
        model, pk_columns = self.get_model_class()

        try:
            # Flatten nested lists into a single-level list of DTOs
            flat_items = items # ListFlattener.flatten(items)

            # Remove any None values from the list
            valid_items = [item for item in flat_items if item is not None]

            # Merge each DTO into the current session (insert or update)
            for dto in valid_items:
                session.merge(model.from_dto(dto))

            # Log the number of successfully saved items
            if len(valid_items) > 0:
                self.logger.log(
                    f"Saved {len(valid_items)} items",
                    level="info",
                )
        except Exception as e:
            # Log the failure reason
            self.logger.log(
                f"Failed to save items: {e}",
                level="error",
            )

            # Re-raise the exception to propagate the error
            raise

    def iter_existing_by_columns(
        self,
        column_names: Union[str, List[str]],
        *,
        uow: Uow, 
        batch_size: int | None = None,
        include_nulls: bool = False,
        distinct: bool = False,
    ) -> Iterator[Tuple]:
        """Stream distinct values for one or more columns in stable order.

        Uses ``yield_per`` to reduce memory pressure and keep deterministic
        ordering. ``stream_results=True`` is kept for consistency; note that
        SQLite does not enable server-side cursors.

        Args:
            column_names (Union[str, List[str]]): Column name or list of names.
            batch_size (int | None): Page size; falls back to repository default.
            include_nulls (bool): Whether to keep rows containing ``NULL``.
                Defaults to ``False``.

        Yields:
            Tuple: Distinct row of selected column values.
        """
        # Resolve page size with repository default
        size = batch_size or self.config.repository.batch_size or 50

        # Resolve model; PK columns are not needed here
        model, _ = self.get_model_class()
        session = uow.session

        # Normalize the column name(s) to a list
        if isinstance(column_names, str):
            column_names = [column_names]

        # Resolve ORM columns from names
        columns = [getattr(model, col) for col in column_names]

        q = session.query(*columns)

        if not include_nulls:
            for c in columns:
                q = q.filter(c.isnot(None))

        if distinct:
            q = q.distinct()

        # Add order_by for stable, deterministic results (especially with distinct and paging)
        q = q.order_by(*columns)

        def yield_rows(rows):
            if len(columns) == 1:
                for v in rows:
                    # SQLAlchemy pode devolver escalar ou (v,) dependendo da versão
                    if isinstance(v, Row):
                        yield (v[0],)
                    elif isinstance(v, tuple):
                        yield v
                    else:
                        try:
                            yield (v[0],)
                        except Exception as e:
                            yield (v,)
            else:
                for r in rows:
                    yield tuple(r) if isinstance(r, tuple) else (r,)

        if size and size > 0:
            offset = 0
            while True:
                chunk = q.offset(offset).limit(size).all()
                if not chunk:
                    break
                yield from yield_rows(chunk)
                offset += size
            return

        rows = q.all()
        yield from yield_rows(rows)

    def get_all_by_columns(
        self,
        column_names: Union[str, List[str], Tuple[str, ...]],
        *,
        uow: Uow,
        include_nulls: bool = False,
        batch_size: int | None = None,
        distinct: bool = False,
    ) -> List[Tuple]:
        """Lista de tuplas com valores de múltiplas colunas.

        Aceita também ``str`` e normaliza para lista com um item.
        Ex.: ``repo.get_all_by_columns(["nsd","version"], uow=uow) -> [(1,"1"), (2,"2"), ...]``
        """
        if isinstance(column_names, str):
            column_names = [column_names]
        return list(
                self.iter_existing_by_columns(
                    list(column_names),
                    uow=uow,
                    include_nulls=include_nulls,
                    batch_size=batch_size,
                    distinct=distinct,
                )
                )

    def get_unique_by_column(
        self,
        column_name: str,
        *,
        uow: Uow,
    ) -> List[Any]:
        """Return all distinct values for a given column.

        Args:
            column_name (str): Name of the ORM column to project.
            uow (Uow): Unit of work providing the SQLAlchemy session.

        Returns:
            List[Any]: Sequence with the distinct values in the requested column.
        """

        model, _ = self.get_model_class()
        column = getattr(model, column_name)

        stmt = select(column).distinct()
        result = uow.session.execute(stmt)
        return [row[0] for row in result]

    def get_all(
        self,
        *,
        uow: Uow,
        batch_size: int | None = None,
    ) -> list[T]:
        """Retorna todos os registros como DTOs."""
        size = batch_size or self.config.repository.batch_size or 50
        model, pk_columns = self.get_model_class()
        session = uow.session

        # Ordena por PK para estabilidade
        order_cols = pk_columns if pk_columns else []
        q = session.query(model)
        if order_cols:
            q = q.order_by(*order_cols)

        # Varre em blocos para não estourar memória, mas materializa tudo no final
        results: list[T] = []
        offset = 0
        while True:
            chunk = q.offset(offset).limit(size).all()
            if not chunk:
                break
            results.extend(m.to_dto() for m in chunk)
            offset += size

        return results

    def get_by_column_values(
        self,
        values: Iterable[tuple[str, Any]] | dict[str, Any],
        *,
        uow: Uow,
        batch_size: int | None = None,  # opcional, apenas para manter padrão
    ) -> list[T]:
        """
        Filtra por uma ou mais colunas com um ou mais valores por coluna.

        Ex.: values=[("code", ["PETR4","VALE3"]), ("source", "BCB")]
        Se o valor for escalar, vira lista. Lista vazia retorna [].
        None dentro da lista significa aceitar NULL na coluna.
        """
        model, pk_columns = self.get_model_class()
        session = uow.session

        # Normaliza dict -> lista de tuplas
        if isinstance(values, dict):
            items = list(values.items())
        else:
            items = list(values)

        if not items:
            # Sem filtros: retorna tudo
            q = session.query(model)
            if pk_columns:
                q = q.order_by(*pk_columns)
            return [m.to_dto() for m in q.all()]

        filters = []
        for col_name, val in items:
            # Normaliza para lista
            if isinstance(val, (list, tuple, set)):
                vals = list(val)
            else:
                vals = [val]

            # Lista vazia implica resultado vazio
            if len(vals) == 0:
                return []

            col = getattr(model, col_name)

            # Separa None de não-None para tratar NULL corretamente
            non_null_vals = [v for v in vals if v is not None]
            wants_null = any(v is None for v in vals)

            exprs = []
            if non_null_vals:
                exprs.append(col.in_(non_null_vals))
            if wants_null:
                exprs.append(col.is_(None))

            # Se só há um termo, usa direto; senão OR entre IN e IS NULL
            if len(exprs) == 1:
                filters.append(exprs[0])
            elif len(exprs) > 1:
                filters.append(or_(*exprs))
            else:
                # Ex.: todos valores eram None mas já tratado acima; por segurança
                filters.append(col.is_(None))

        q = session.query(model).filter(and_(*filters))
        if pk_columns:
            q = q.order_by(*pk_columns)

        return [m.to_dto() for m in q.all()]

    # def get_existing_by_columns(
    #     self, column_names: Union[str, List[str]],
    #     uow: Uow, 
    # ) -> List[Tuple]:
    #     """Return distinct, ordered tuples for one or more given columns.

    #     Examples:
    #         >>> repo.get_existing_by_columns("nsd")
    #         [('94790',), ('12345',)]

    #         >>> repo.get_existing_by_columns(["nsd", "company_name"])
    #         [('12345', 'ROMI'), ('94790', 'ACME')]

    #     Args:
    #         column_names (Union[str, List[str]]): Single column name or a list
    #             of column names to retrieve.

    #     Returns:
    #         List[Tuple]: Distinct and ordered tuples of the requested columns.
    #     """
    #     # Open a session for the read-only operation
    #     session = uow.session()

    #     # Retrieve the SQLAlchemy model class associated with the DTO type
    #     model, pk_columns = self.get_model_class()

    #     try:
    #         # Normalize column_names to a list
    #         if isinstance(column_names, str):
    #             column_names = [column_names]

    #         # Resolve ORM columns to select
    #         kw_columns = [getattr(model, name) for name in column_names]

    #         # Fetch distinct values (unordered by default)
    #         rows = session.query(*kw_columns).distinct().all()

    #         # Remove rows that contain any NULL field
    #         results = [row for row in rows if not any(field is None for field in row)]

    #         # Create a lightweight wrapper to simulate attribute access on a tuple
    #         class RowWrapper:
    #             def __init__(self, values):
    #                 # Store the original tuple of values
    #                 self._values = values

    #             def __getattr__(self, key):
    #                 # Find the index of the requested column name
    #                 idx = column_names.index(key)
    #                 # Return the value at that index in the tuple
    #                 return self._values[idx]

    #         # Sort using the repository's robust PK-aware key function
    #         results.sort(
    #             key=lambda row:
    #             # Wrap the tuple to enable attribute-style access
    #             self._sort_key(RowWrapper(row), kw_columns)
    #         )

    #         # Return the cleaned and sorted tuples
    #         return results
    #     finally:
    #         # Ensure the session is closed
    #         session.close()

    # def _safe_cast(self, value: Any) -> Union[int, str]:
    #     """Convert to ``int`` when possible; otherwise return the original as ``str``."""
    #     try:
    #         return int(value)
    #     except (ValueError, TypeError):
    #         return str(value)

    # def _sort_key(self, obj: Any, pk_columns: Sequence) -> tuple[Union[int, str], ...]:
    #     """Build a numeric-aware tuple key from object attributes.

    #     Ensures mixed numeric/string PKs sort consistently by attempting integer
    #     casts first and falling back to string comparison.

    #     Args:
    #         obj (Any): An object exposing attributes with names matching ``pk_columns``.
    #         pk_columns (Sequence): Column expressions whose ``.key`` names are used
    #             to access attributes on ``obj``.

    #     Returns:
    #         tuple[Union[int, str], ...]: Composite sort key suitable for ``list.sort``.
    #     """
    #     return tuple(self._safe_cast(getattr(obj, col.key)) for col in pk_columns)

    # def get_all(self, batch_size: int = 100) -> List[T]:
    #     """Retrieve all DTOs using keyset pagination over the primary key.

    #     Fetches data incrementally to avoid loading the entire dataset into
    #     memory. Falls back to a repository-configured default when
    #     ``batch_size`` is not provided.

    #     Args:
    #         batch_size (int): Number of rows to fetch per loop iteration.

    #     Returns:
    #         List[T]: All DTOs retrieved from the database in ascending PK order.
    #     """
    #     # batch_size = batch_size or self.config.global_settings.batch_size

    #     # # Create a new SQLAlchemy session
    #     # session = self.Session()

    #     # # Get the SQLAlchemy model class linked to the current DTO type
    #     # model, pk_columns = self.get_model_class()

    #     # all_results: List[T] = []
    #     # last_id = 0

    #     # while True:
    #     #     batch = (
    #     #         session.query(model)
    #     #         .filter(model.id > last_id)
    #     #         .order_by(model.id)
    #     #         .limit(batch_size)
    #     #         .all()
    #     #     )

    #     #     if not batch:
    #     #         break

    #     #     all_results.extend([m.to_dto() for m in batch])
    #     #     last_id = batch[-1].id
    #     # return all_results
    #     # Resolve batch size with repository default as fallback
    #     batch_size = batch_size or self.config.repository.batch_size or 50

    #     # Resolve model and PK columns for pagination
    #     model, pk_columns = self.get_model_class()

    #     # Accumulate results progressively
    #     all_results: List[T] = []

    #     # Track the last seen key for keyset pagination
    #     last_key: Optional[Union[int, str]] = None

    #     # Use an explicit session scope for clarity
    #     session = self.Session()
    #     try:
    #         while True:
    #             # Use the first PK column for ordering; composite handled elsewhere
    #             col = pk_columns[0]

    #             # Start with base query for the model
    #             q = session.query(model)

    #             # Apply keyset continuation when a last key exists
    #             if last_key is not None:
    #                 q = q.filter(col > last_key)

    #             # Order by PK and cap the page size
    #             batch = q.order_by(col).limit(batch_size).all()

    #             # Terminate when no further rows are returned
    #             if not batch:
    #                 break

    #             # Convert ORM models to DTOs and append to results
    #             all_results.extend(m.to_dto() for m in batch)

    #             # Advance the cursor to the last seen key
    #             last_key = getattr(batch[-1], col.key)

    #         # Return the complete materialized list
    #         return all_results
    #     finally:
    #         # Ensure the session is closed
    #         session.close()

    # def iter_all(self, batch_size: int | None = None) -> Generator[T, None, None]:
    #     """Yield DTOs lazily using keyset pagination (simple or composite PK).

    #     Args:
    #         batch_size (int | None): Page size; falls back to repository default.

    #     Yields:
    #         T: DTOs sequentially in deterministic primary-key order.
    #     """
    #     # Resolve page size with repository default
    #     size = batch_size or self.config.repository.batch_size or 50

    #     # Resolve model and PK columns to pick the iteration strategy
    #     model, pk_columns = self.get_model_class()

    #     # Track how many items were produced (for potential logging)
    #     yielded = 0
    #     try:
    #         # Choose strategy based on PK arity
    #         if len(pk_columns) == 1:
    #             gen = self._iter_all_simple(size)
    #         else:
    #             gen = self._iter_all_composite(size)

    #         # Stream results from the chosen generator
    #         for dto in gen:
    #             yielded += 1
    #             yield dto
    #     finally:
    #         # Reserved for optional structured logging
    #         pass

    # def _iter_all_simple(self, size: int) -> Generator[T, None, None]:
    #     """Internal generator for single-column PK keyset iteration."""
    #     # Resolve model and the single PK column
    #     model, pk_columns = self.get_model_class()
    #     col = pk_columns[0]

    #     # Track the last emitted key to resume the window
    #     last_key: Optional[Any] = None
    #     with self.Session() as session:
    #         # Build a shared base query with streaming-friendly options
    #         base_q = (
    #             session.query(model)
    #             .order_by(col)
    #             .yield_per(size)
    #             .execution_options(stream_results=True)
    #             .enable_eagerloads(False)
    #         )

    #         # Iterate until the window produces no rows
    #         while True:
    #             q = base_q

    #             # Resume after the last emitted key
    #             if last_key is not None:
    #                 q = q.filter(col > last_key)

    #             # Count rows to determine loop termination
    #             count = 0

    #             # Limit per page to avoid large buffers
    #             for m in q.limit(size):
    #                 # Convert ORM model to DTO
    #                 yield m.to_dto()

    #                 # Advance the last key
    #                 last_key = getattr(m, col.key)
    #                 count += 1

    #             # Stop when no rows were produced in this pass
    #             if count == 0:
    #                 break

    # def _iter_all_composite(self, size: int) -> Generator[T, None, None]:
    #     """Internal generator for composite-PK keyset iteration."""
    #     # Resolve model and composite PK columns
    #     model, pk_columns = self.get_model_class()

    #     # Track the last emitted composite key as tuple
    #     last_key: Optional[Tuple] = None
    #     with self.Session() as session:
    #         # Build a shared base query with streaming-friendly options
    #         base_q = (
    #             session.query(model)
    #             .order_by(*pk_columns)
    #             .yield_per(size)
    #             .execution_options(stream_results=True)
    #             .enable_eagerloads(False)
    #         )

    #         # Iterate windows until exhausted
    #         while True:
    #             q = base_q

    #             # Resume after the last emitted composite key
    #             if last_key is not None:
    #                 q = q.filter(sa_tuple(*pk_columns) > sa_tuple(*last_key))

    #             # Count rows to determine loop termination
    #             count = 0

    #             # Limit per page to avoid large buffers
    #             for m in q.limit(size):
    #                 # Convert ORM model to DTO
    #                 yield m.to_dto()

    #                 # Capture the composite key for resume
    #                 last_key = tuple(getattr(m, c.key) for c in pk_columns)
    #                 count += 1

    #             # Stop when no rows were produced in this pass
    #             if count == 0:
    #                 break

    # def get_all_primary_keys(self) -> List[str]:
    #     """Return all unique primary keys in ascending order.

    #     Queries distinct values over the primary key columns and returns the
    #     first column as a list of strings (e.g., CVM codes).

    #     Returns:
    #         List[str]: Unique primary key values in deterministic order.
    #     """
    #     # Create a new SQLAlchemy session
    #     session = self.Session()

    #     # Get the SQLAlchemy model class linked to the current DTO type
    #     model, pk_columns = self.get_model_class()

    #     try:
    #         # Execute a distinct query for the primary key columns
    #         results = session.query(*pk_columns).distinct().order_by(*pk_columns).all()

    #         # Sort by PK using a robust tuple key (numeric-aware)
    #         results.sort(key=lambda obj: self._sort_key(obj, pk_columns))

    #         # Extract and collect non-null first-column keys into a list
    #         return [row[0] for row in results if row[0]]

    #     finally:
    #         # Ensure session is always closed
    #         session.close()

    # def has_item(self, identifier: K) -> bool:
    #     """Check whether a record with the given identifier exists.

    #     Supports both single-column and composite primary keys.

    #     Args:
    #         identifier (K): Either a scalar (single PK) or a tuple (composite PK).

    #     Returns:
    #         bool: ``True`` if a matching row exists, otherwise ``False``.
    #     """
    #     # Create a new SQLAlchemy session
    #     session = self.Session()

    #     # Get the SQLAlchemy model class linked to the current DTO type
    #     model, pk_columns = self.get_model_class()

    #     try:
    #         # Build filter for single or composite primary keys
    #         if len(pk_columns) == 1:
    #             filter_expr = pk_columns[0] == identifier
    #         else:
    #             assert isinstance(identifier, tuple), "Expected tuple for composite key"
    #             filter_expr = [col == val for col, val in zip(pk_columns, identifier)]

    #         # Apply the appropriate filter shape
    #         query = (
    #             session.query(model).filter(*filter_expr)
    #             if isinstance(filter_expr, list)
    #             else session.query(model).filter(filter_expr)
    #         )

    #         # Existence check using first-row presence
    #         return query.first() is not None
    #     finally:
    #         # Always close the session after the query
    #         session.close()

    # def get_by_id(self, identifier: K) -> T:
    #     """Retrieve a DTO by its primary key, raising if not found.

    #     Handles both single-column and composite PK lookups.

    #     Args:
    #         identifier (K): Either a scalar (single PK) or a tuple (composite PK).

    #     Returns:
    #         T: The DTO corresponding to the provided primary key.

    #     Raises:
    #         ValueError: If no record is found for the given identifier.
    #     """
    #     # Create a new SQLAlchemy session
    #     session = self.Session()

    #     # Get the SQLAlchemy model class linked to the current DTO type
    #     model, pk_columns = self.get_model_class()

    #     try:
    #         # Build filter for single or composite primary keys
    #         if len(pk_columns) == 1:
    #             filter_expr = pk_columns[0] == identifier
    #         else:
    #             assert isinstance(identifier, tuple), "Expected tuple for composite key"
    #             filter_expr = [col == val for col, val in zip(pk_columns, identifier)]

    #         # Apply the appropriate filter shape
    #         query = (
    #             session.query(model).filter(*filter_expr)
    #             if isinstance(filter_expr, list)
    #             else session.query(model).filter(filter_expr)
    #         )

    #         # Fetch the object or raise a not-found error
    #         obj = query.first()
    #         if not obj:
    #             raise ValueError(f"Data not found: {identifier}")

    #         # Convert ORM model to DTO and return
    #         return obj.to_dto()
    #     finally:
    #         # Ensure the session is closed in all cases
    #         session.close()

    # def get_by_column_values(
    #     self,
    #     column_names: Union[str, List[str]],
    #     values: Union[Any, List[Any]],
    # ) -> List[T]:
    #     """Filter records by one or more columns with flexible value semantics.

    #     Empty filters (``None``, empty string, or ``[]``) are treated as
    #     "match any" and removed from the condition. For a single column, the
    #     filter uses ``IN`` semantics. For multiple columns, the function builds
    #     the cartesian product of active column values and filters using a
    #     tuple ``IN`` expression.

    #     Examples:
    #         >>> get_by_column_values(["company_name", "nsd_type"], [["ACME", "ROMI"], ""])
    #         -- Equivalent to: WHERE company_name IN ('ACME', 'ROMI')

    #         >>> get_by_column_values("nsd_type", ["A", "B"])
    #         -- Equivalent to: WHERE nsd_type IN ('A', 'B')

    #     Args:
    #         column_names (Union[str, List[str]]): Single column name or list of names.
    #         values (Union[Any, List[Any]]): Single value, list of values, or
    #             list-of-lists where each inner list corresponds to one column.

    #     Returns:
    #         List[T]: DTOs that satisfy the constructed filter.
    #     """
    #     # Open a session for the read-only operation
    #     session = self.Session()

    #     # Resolve ORM model; PK columns are not required
    #     model, _ = self.get_model_class()

    #     try:
    #         # Normalize column_names to a list
    #         if isinstance(column_names, str):
    #             column_names = [column_names]

    #         # Normalize values to a list
    #         if not isinstance(values, list):
    #             values = [values]

    #         # For single-column case, ensure values is a list-of-lists
    #         if len(column_names) == 1 and (not any(isinstance(v, list) for v in values)):
    #             values = [values]

    #         # Build active filters per column, skipping "empty" values
    #         normalized_values = []
    #         active_columns = []
    #         for col, val in zip(column_names, values):
    #             if isinstance(val, list):
    #                 clean = [v for v in val if v not in (None, '')]
    #             else:
    #                 clean = [val] if val not in (None, '') else []

    #             if clean:
    #                 active_columns.append(col)
    #                 normalized_values.append(clean)

    #         # If no filters remain active, return all rows
    #         if not active_columns:
    #             return [obj.to_dto() for obj in session.query(model).all()]

    #         # Single-column IN filter
    #         if len(active_columns) == 1:
    #             col = getattr(model, active_columns[0])
    #             query_filter = col.in_(normalized_values[0])
    #         else:
    #             # Multi-column tuple IN over cartesian combinations
    #             cols = [getattr(model, c) for c in active_columns]
    #             combinations = list(product(*normalized_values))
    #             if not combinations:
    #                 return []
    #             query_filter = sa_tuple(*cols).in_(combinations)

    #         # Execute the filtered query and convert to DTOs
    #         results = session.query(model).filter(query_filter).all()
    #         return [obj.to_dto() for obj in results]

    #     finally:
    #         # Ensure the session is closed
    #         session.close()

    # def get_page_after(self, last_id: int, limit: int) -> List[T]:
    #     """Return one page of DTOs ordered by the surrogate ``id`` column.

    #     Args:
    #         last_id (int): The last seen surrogate identifier.
    #         limit (int): Maximum number of rows to return.

    #     Returns:
    #         List[T]: A page of DTOs strictly after ``last_id``.
    #     """
    #     # Use a short-lived session for this paginated read
    #     session = self.Session()

    #     # Resolve model and PK columns; the method uses a surrogate id column
    #     model, pk_columns = self.get_model_class()
    #     try:
    #         # Keyset-style page strictly after the provided surrogate id
    #         query = (
    #             session.query(model)
    #             .filter(model.id > last_id)
    #             .order_by(model.id)
    #             .limit(limit)
    #         )

    #         # Convert all ORM rows to DTOs
    #         return [obj.to_dto() for obj in query.all()]
    #     finally:
    #         # Close the session
    #         session.close()
