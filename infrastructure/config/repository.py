from __future__ import annotations

from dataclasses import dataclass, field

BATCH_SIZE = 100
persistence_threshold = 10 # (MAX_WORKERS)  # max(int(50 / MAX_WORKERS), 1)  # Default threshold for saving data


@dataclass(frozen=True)
class RepositoryConfig:

    batch_size: int = field(default=BATCH_SIZE)
    persistence_threshold: int = field(default=persistence_threshold)

def load_repository_config() -> RepositoryConfig:
    return RepositoryConfig(
        batch_size=BATCH_SIZE,
        persistence_threshold=persistence_threshold,
    )
