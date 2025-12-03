from __future__ import annotations

from dataclasses import dataclass, field

# Default batch size for repository operations
BATCH_SIZE = 50

# Default persistence threshold (how often data should be committed)
# Originally could depend on MAX_WORKERS (e.g., max(int(50 / MAX_WORKERS), 1))
PERSISTENCE_THRESHOLD = 3


@dataclass(frozen=True)
class RepositoryConfig:
    """Immutable configuration for repository behavior.

    Attributes:
        batch_size (int): Number of items to process in a single batch.
        persistence_threshold (int): Threshold for triggering persistence
            (e.g., number of operations before saving to storage).
    """

    # Number of items to group per batch
    batch_size: int = field(default=BATCH_SIZE)

    # Minimum threshold for persistence
    persistence_threshold: int = field(default=PERSISTENCE_THRESHOLD)


def load_repository_config() -> RepositoryConfig:
    """Factory function to load repository configuration.

    Returns:
        RepositoryConfig: Initialized with default batch size and
        persistence threshold.
    """
    # Construct and return repository configuration with defaults
    return RepositoryConfig(
        batch_size=BATCH_SIZE,
        persistence_threshold=PERSISTENCE_THRESHOLD,
    )
