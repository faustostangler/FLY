from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

# # Default folder name created under the project root for cached artifacts
# CACHE_DIR_NAME = "cache"

# # Default SQLite database filename used to persist cache metadata
# DB_CACHE_FILENAME = "fly_cache.db"

# # Default table name storing cache metadata
# CACHE_TABLE_NAME = "tbl_cache"

# Default maximum on-disk size (in bytes) before eviction kicks in (1 GB)
MAX_CACHE_SIZE_BYTES = 1_000_000_000

# Default age threshold (in days) before entries are considered stale
MAX_AGE_DAYS = 30

# Default parquet compression codec
PARQUET_COMPRESSION = "zstd"


@dataclass(frozen=True)
class CachePolicy:
    """Configuration describing how the ratios cache behaves and where it lives."""

    # base_dir: Path
    # db_filename: str = field(default=DB_CACHE_FILENAME)
    # table_name: str = field(default=CACHE_TABLE_NAME)
    # connection_string: str = field(init=False)
    max_cache_size_bytes: int = field(default=MAX_CACHE_SIZE_BYTES)
    max_age_days: int = field(default=MAX_AGE_DAYS)
    parquet_compression: str = field(default=PARQUET_COMPRESSION)
    max_age: timedelta = field(init=False)

    def __post_init__(self) -> None:
        # Ensure the base directory exists for both parquet files and the SQLite DB
        # base_dir = Path(self.base_dir)
        # base_dir.mkdir(parents=True, exist_ok=True)

        # object.__setattr__(self, "base_dir", base_dir)
        # object.__setattr__(
        #     self,
        #     "connection_string",
        #     f"sqlite:///{base_dir / self.db_filename}",
        # )
        object.__setattr__(
            self,
            "max_age",
            timedelta(days=self.max_age_days),
        )


