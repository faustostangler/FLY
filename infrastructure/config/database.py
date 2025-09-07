from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from infrastructure.config.paths import load_paths

# Default SQLite database filename
DB_FILENAME = "fly.db"

# Logical-to-physical table name mapping for SQLite
TABLES = {
    "company": "tbl_company",
    "nsd": "tbl_nsd",
    "raw_statements": "tbl_raw_statements",
    "fetched_statements": "tbl_statements_fetched",
}


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

    # Mapping of logical table keys to physical table names
    tables: Mapping[str, str] = field(default_factory=lambda: TABLES)

    # SQLAlchemy-compatible connection string (computed in __post_init__)
    connection_string: str = field(init=False)

    def __post_init__(self) -> None:
        """Compute and assign the SQLite connection string after initialization."""
        # Dynamically build a SQLAlchemy-compatible SQLite URI
        object.__setattr__(
            self,
            "connection_string",
            f"sqlite:///{self.data_dir / self.db_filename}",
        )


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
        tables=TABLES,
    )
