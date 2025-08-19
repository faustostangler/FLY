from __future__ import annotations

from dataclasses import dataclass, field

BATCH_SIZE = 100


@dataclass(frozen=True)
class RepositoryConfig:

    batch_size: int = field(default=BATCH_SIZE)

def load_repository_config() -> RepositoryConfig:
    return RepositoryConfig(
        batch_size=BATCH_SIZE,
    )
