from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from infrastructure.config.paths import load_paths

# Default SQLite database filename
DB_FILENAME = "fly.db"
DB_CACHE_FILENAME = "fly_cache.db"

# Logical-to-physical table name mapping for SQLite
TABLES = {
    "company": "tbl_company",
    "nsd": "tbl_nsd",
    "raw_statements": "tbl_statements_raw",
    "fetched_statements": "tbl_statements_fetched",
}

def _sqlite_uri(db_path: Path) -> str:
    # string única e padronizada
    return f"sqlite:///{db_path.as_posix()}"

@dataclass(frozen=True)
class DatabaseConfig:
    """Immutable configuration object for the database.

    Attributes:
        data_dir (Path): Directory where the SQLite database file is stored.
        db_filename (str): Name of the SQLite database file (default: `fly.db`).
        tables (Mapping[str, str]): Mapping of logical table identifiers
            to their corresponding SQLite table names.
        connection_string (str): SQLAlchemy-style connection string
            used to establish database connections.
    """

    # Directory that holds the database file
    data_dir: Path

    # Name of the database file (default: fly.db)
    db_filename: str = field(default=DB_FILENAME)
    db_cache_filename: str = field(default=DB_CACHE_FILENAME)

    # Mapping of logical table keys to physical table names
    tables: Mapping[str, str] = field(default_factory=lambda: TABLES)

    # SQLAlchemy-compatible connection string (computed in __post_init__)
    @property
    def connection_string(self) -> str:
        return _sqlite_uri(self.data_dir / self.db_filename)

    @property
    def connection_cache_string(self) -> str:  # novo
        # repare: usa paths.cache_dir, não data_dir raiz
        paths = load_paths()
        return _sqlite_uri(paths.cache_dir / self.db_cache_filename)

def load_database_config() -> DatabaseConfig:
    """Factory function to load the database configuration.

    Retrieves project-defined paths and builds a fully initialized
    database configuration object.

    Returns:
        DatabaseConfig: Immutable configuration with directory, filename,
        tables mapping, and connection string.
    """
    # Get project-level paths from global configuration
    paths = load_paths()

    # Construct and return the database configuration object
    return DatabaseConfig(
        data_dir=paths.data_dir,
        db_filename=DB_FILENAME,
        db_cache_filename=DB_CACHE_FILENAME,  # novo
        tables=TABLES,
    )
