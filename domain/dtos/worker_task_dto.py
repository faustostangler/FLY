from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkerTaskDTO:
    """Data Transfer Object (DTO) representing a unit of work for a worker.

    Attributes:
        index (int): Sequential index of the task within the job queue.
        data (Any): Payload or content that the worker must process.
        worker_id (str): Identifier of the worker responsible for handling the task.
    """

    # Sequential index of the task
    index: int

    # Arbitrary payload assigned to the worker
    data: Any

    # Worker identifier to track assignment or ownership
    worker_id: str

    # Total Worker Batch Size
    total_size: int | None = None