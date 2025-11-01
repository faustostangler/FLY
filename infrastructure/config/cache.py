from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import timedelta

from infrastructure.config.paths import load_paths

# Default folder name created under the project root for cached artifacts
CACHE_DIR_NAME = "cache"

# Default SQLite database filename used to persist cache metadata
CACHE_DB_FILENAME = "fly_cache.db"

# Default table name storing cache metadata
CACHE_TABLE_NAME = "tbl_cache"

# Default maximum on-disk size (in bytes) before eviction kicks in (1 GB)
MAX_CACHE_SIZE_BYTES = 1_000_000

# Default age threshold (in days) before entries are considered stale
MAX_AGE_DAYS = 30

# Default parquet compression codec
PARQUET_COMPRESSION = "zstd"


@dataclass(frozen=True)
class CacheConfig:
    """Configuration describing how the ratios cache behaves and where it lives."""

    base_dir: Path
    db_filename: str = field(default=CACHE_DB_FILENAME)
    table_name: str = field(default=CACHE_TABLE_NAME)
    max_cache_size_bytes: int = field(default=MAX_CACHE_SIZE_BYTES)
    max_age_days: int = field(default=MAX_AGE_DAYS)
    parquet_compression: str = field(default=PARQUET_COMPRESSION)
    connection_string: str = field(init=False)
    max_age: timedelta = field(init=False)

    def __post_init__(self) -> None:
        # Ensure the base directory exists for both parquet files and the SQLite DB
        base_dir = Path(self.base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)

        object.__setattr__(self, "base_dir", base_dir)
        object.__setattr__(
            self,
            "connection_string",
            f"sqlite:///{base_dir / self.db_filename}",
        )
        object.__setattr__(
            self,
            "max_age",
            timedelta(days=self.max_age_days),
        )


def load_cache_config() -> CacheConfig:
    """Build a :class:`CacheConfig` using project defaults."""

    paths = load_paths()
    return CacheConfig(base_dir=paths.root_dir / CACHE_DIR_NAME)
