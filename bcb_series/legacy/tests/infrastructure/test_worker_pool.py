from domain.dto import MetricsDTO, WorkerTaskDTO
from infrastructure.helpers.worker_pool import WorkerPool
from tests.conftest import DummyConfig, DummyLogger


class DummyMetricsCollector:
    def __init__(self) -> None:
        self.network_bytes = 0
        self.processing_bytes = 0

    def record_network_bytes(self, n: int) -> None:
        self.network_bytes += n

    def record_processing_bytes(self, n: int) -> None:
        self.processing_bytes += n

    def get_metrics(self, elapsed_time: float) -> MetricsDTO:
        return MetricsDTO(
            elapsed_time=elapsed_time,
            network_bytes=self.network_bytes,
            processing_bytes=self.processing_bytes,
        )


def test_worker_pool_passes_task_dto():
    collector = DummyMetricsCollector()
    pool = WorkerPool(config=DummyConfig(), metrics_collector=collector)

    tasks = list(
        enumerate(
            [
                {"codeCVM": "A"},
                {"codeCVM": "B"},
                {"codeCVM": "C"},
            ]
        )
    )
    received = []

    def processor(task: WorkerTaskDTO) -> str:
        assert isinstance(task, WorkerTaskDTO)
        received.append((task.index, task.data, task.worker_id))
        return task.data

    result = pool.run(tasks=tasks, processor=processor, logger=DummyLogger())

    assert result.items == [
        {"codeCVM": "A"},
        {"codeCVM": "B"},
        {"codeCVM": "C"},
    ]
    assert len(received) == len(tasks)
    for idx, data, worker_id in received:
        assert tasks[idx][1] == data
        assert worker_id
