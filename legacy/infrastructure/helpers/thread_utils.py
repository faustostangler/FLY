import threading

from domain.ports import ConfigPort


class WorkerThreadIdentifier:
    """Generate readable, unique identifiers for worker threads.

    Example identifiers: ``"W1"``, ``"W2"``, up to the ``max_workers`` limit from ``Config``.
    """

    def __init__(self, config: ConfigPort) -> None:
        """Initialize the generator using the configured ``max_workers`` value.

        Args:
            config: Application configuration with ``max_workers``.
        """
        self._max_workers = config.global_settings.max_workers or 1
        self._thread_local = threading.local()
        self._counter = iter(range(1, self._max_workers + 1))

    def get_worker_name(self) -> str:
        """Return a unique worker name for the current thread.

        Returns:
            str: A name such as ``"W1"`` or ``"W2"`` reused while the thread lives.
        """
        if not hasattr(self._thread_local, "worker_name"):
            self._thread_local.worker_name = f"W{next(self._counter)}"
        # return self._thread_local.worker_name
        return str(threading.get_ident())
