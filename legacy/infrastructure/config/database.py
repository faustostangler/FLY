# settings/database.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .paths import load_paths

DB_FILENAME = "fly.db"
TABLES = {
    # logic key : SQLite physical name
    "company": "tbl_company",
    "nsd": "tbl_nsd",
    "raw_statements": "tbl_raw_statements",
    "parsed_statements": "tbl_parsed_statements",
}


@dataclass(frozen=True)
class DatabaseConfig:
    """SQLite database configuration.

    Attributes:
        data_dir: Directory where the database file is stored.
        db_file_name: SQLite file name.
        db_path: Full path to the database file.
        connection_string: SQLAlchemy connection URI.
    """

    data_dir: Path
    db_filename: str = field(default=DB_FILENAME)
    tables: Mapping[str, str] = field(default_factory=lambda: TABLES)
    connection_string: str = field(init=False)

    def __post_init__(self) -> None:
        # Dynamically compute the connection URI
        object.__setattr__(
            self, "connection_string", f"sqlite:///{self.data_dir / self.db_filename}"
        )


def load_database_config() -> DatabaseConfig:
    """Run the database configuration using project paths."""

    paths = load_paths()

    return DatabaseConfig(
        data_dir=paths.data_dir,
        db_filename=DB_FILENAME,
        tables=TABLES,
    )
