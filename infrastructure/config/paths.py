from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path

# Named subfolders that will be created under the project root
TEMP_DIR = "temp"
LOG_DIR = "logs"
DATA_DIR = "data"
CACHE_DIR = "cache"

@dataclass(frozen=True)
class PathConfig:
    """Resolved filesystem paths for the application.

    The paths are derived from the project root and created on initialization
    if they do not already exist. All attributes are computed in ``__post_init__``
    and the dataclass is frozen to keep them immutable after construction.

    Attributes:
        temp_dir (Path): Directory for temporary artifacts.
        log_dir (Path): Directory where log files are written.
        data_dir (Path): Directory for application data (e.g., databases, exports).
        root_dir (Path): Project root directory (one level above the package root).
    """

    # Computed absolute path to the project root directory
    root_dir: Path = field(default_factory=lambda: Path.cwd())

    # Computed path to the temp directory under the project root
    temp_dir: Path = field(init=False)

    # Computed path to the logs directory under the project root
    log_dir: Path = field(init=False)

    # Computed path to the data directory under the project root
    data_dir: Path = field(init=False)

    # Computed path to the data directory under the project root
    cache_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        """Resolve paths from the project root and ensure required folders exist."""
        # Resolve the project root (package/__file__/.../ -> project root)
        root = Path(__file__).resolve().parent.parent.parent

        # Assign resolved root and derived subdirectories
        object.__setattr__(self, "temp_dir", root / TEMP_DIR)
        object.__setattr__(self, "log_dir", self.root_dir / LOG_DIR)
        object.__setattr__(self, "data_dir", self.root_dir / DATA_DIR)
        object.__setattr__(self, "cache_dir", self.data_dir / CACHE_DIR)

        # Ensure all non-root directories exist (idempotent)
        for fld in fields(self):
            p = getattr(self, fld.name)
            if isinstance(p, Path) and fld.name != "root_dir":
                p.mkdir(parents=True, exist_ok=True)


def load_paths() -> PathConfig:
    """Create and return a ``PathConfig`` with ensured directories.

    Returns:
        PathConfig: Immutable object with resolved root, temp, log, and data paths.
    """
    # Instantiate the configuration, which also ensures directories are present
    return PathConfig()
