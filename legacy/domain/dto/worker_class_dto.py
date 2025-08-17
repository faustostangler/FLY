from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkerTaskDTO:
    index: int
    data: Any
    worker_id: str
