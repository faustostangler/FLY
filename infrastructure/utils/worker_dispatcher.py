# infrastructure/utils/worker_dispatcher.py
import json, threading, time
from typing import Callable, Dict, Type, Any
from domain.events.events import NSDReady, StatementsFetched

EVENT_TYPES: Dict[str, Type[Any]] = {"NSDReady": NSDReady, "StatementsFetched": StatementsFetched}

class OutboxDispatcherWorker:
    def __init__(self, session_factory: Callable, outbox_repo_factory: Callable, event_bus, batch_size: int = 50, idle_sleep: float = 0.5):
        self._session_factory = session_factory
        self._outbox_repo_factory = outbox_repo_factory
        self._bus = event_bus
        self._batch_size = batch_size
        self._idle_sleep = idle_sleep
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="OutboxDispatcher", daemon=True)
        self._thread.start()

    def stop(self, timeout: float | None = None) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        sleep_cur = self._idle_sleep
        while not self._stop.is_set():
            with self._session_factory() as s:
                repo = self._outbox_repo_factory(s)
                rows = repo.fetch_available(self._batch_size)
                if not rows:
                    time.sleep(sleep_cur)
                    sleep_cur = min(sleep_cur * 1.5, 2.0)
                    continue
                sleep_cur = self._idle_sleep
                for row in rows:
                    try:
                        payload = json.loads(row.payload_json)
                        evt_cls = EVENT_TYPES[payload["type"]]
                        evt = evt_cls(**payload["data"])
                        self._bus.publish(row.topic, evt)
                        repo.mark_published(row)
                    except Exception:
                        repo.mark_failed(row)
                s.commit()
