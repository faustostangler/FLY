from dataclasses import dataclass, field, fields
from pathlib import Path

# Subpastas nomeadas (relativas ao root)
TEMP_DIR = "temp"
LOG_DIR = "logs"
DATA_DIR = "data"


@dataclass(frozen=True)
class PathConfig:
    """Configuration for important filesystem paths.

    Attributes:
        root_dir: Absolute project root directory (computed automatically).
        temp_dir: Subfolder for temporary files.
        log_dir: Subfolder for log files.
        data_dir: Subfolder for databases.
    """

    temp_dir: Path = field(init=False)
    log_dir: Path = field(init=False)
    data_dir: Path = field(init=False)
    root_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        # Set root_dir to the project directory
        root = Path(__file__).resolve().parent.parent.parent
        object.__setattr__(self, "root_dir", root)
        object.__setattr__(self, "temp_dir", root / TEMP_DIR)
        object.__setattr__(self, "log_dir", root / LOG_DIR)
        object.__setattr__(self, "data_dir", root / DATA_DIR)

        # Create folders if they do not already exist
        for fld in fields(self):
            p = getattr(self, fld.name)
            if isinstance(p, Path) and fld.name != "root_dir":
                p.mkdir(parents=True, exist_ok=True)


def load_paths() -> PathConfig:
    """Create and return a ``PathConfig`` instance with ensured directories."""

    return PathConfig()
