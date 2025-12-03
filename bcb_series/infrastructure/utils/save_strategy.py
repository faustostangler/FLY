from __future__ import annotations

from dataclasses import dataclass, field

# <<<<<<< codex/fix-uow-propagation-in-companydatascraper-3sz01n
from typing import Generic, Iterable, List, Optional, TypeVar

# =======
# from typing import Generic, Iterable, List, Optional, TypeVar, Protocol
# >>>>>>> 2025-09-09-Fetch-Adjustments
from application.ports.config_port import ConfigPort
from application.ports.uow_port import Uow, UowFactoryPort
from domain.ports.scraper_base_port import SaveCallback

T = TypeVar("T")

# <<<<<<< codex/fix-uow-propagation-in-companydatascraper-3sz01n
# =======
# class SaveCallback(Protocol, Generic[T]):
#     def __call__(self, items: List[T], *, uow: Uow) -> None: ...

# >>>>>>> 2025-09-09-Fetch-Adjustments

@dataclass
class SaveStrategy(Generic[T]):
    """Batching strategy that buffers items and persists them in chunks.

    This class accumulates items in memory and invokes a user-provided
    callback once the buffer size reaches a configured threshold. It helps
    reduce I/O overhead by performing bulk writes.

    Type Variables:
        T: The item type to be buffered and persisted.

    Attributes:
        save_callback (SaveCallback[T]): Function invoked when the
            buffer is flushed; receives the current buffered items.
        threshold (int): Maximum number of items to buffer before triggering
            a flush.
        _buffer (List[T]): Internal, mutable buffer of pending items.
    """

    # Callback invoked when a flush occurs
    save_callback: SaveCallback[T]

    # Maximum number of items to accumulate before flushing
    threshold: int

    # Uow factory for creating unit of work contexts
    uow_factory: UowFactoryPort

    # False to avoid partial flush by threshold (True to allow partial flush)
    auto_flush: bool = True

    # Internal buffer holding pending items
    _buffer: List[T] = field(default_factory=list)

    @classmethod
    def from_config(
        cls,
        save_callback: SaveCallback[T] | None = None,
        threshold: Optional[int] = None,
        config: Optional[ConfigPort] = None,
        auto_flush: bool = True,
        uow_factory: Optional[UowFactoryPort] = None,
    ) -> "SaveStrategy[T]":
        """Create a strategy using explicit args or fall back to configuration.

        Resolution order:
        1) Use explicit `save_callback` / `threshold` if provided.
        2) Otherwise, derive `threshold` from `config.repository.persistence_threshold`.
        3) Default to a no-op callback and a safe threshold if neither is provided.

        Args:
            save_callback: Function to call on flush; if None, a no-op is used.
            threshold: Explicit batch size; if None, try to read from `config`.
            config: Optional configuration source that can provide a threshold.

        Returns:
            SaveStrategy[T]: A strategy instance ready to buffer and flush items.
        """
        # Choose a callback or fall back to a no-op implementation
        cb: SaveCallback[T] = save_callback or (lambda items, *, uow: None)

        # Choose a threshold from explicit arg, config, or a conservative default
        th = threshold or (config.repository.persistence_threshold if config else 50)

        # Build and return the configured strategy
        if uow_factory is None:
            raise ValueError("SaveStrategy precisa de uow_factory")

        return cls(cb, th, uow_factory)

    def handle(self, item: T) -> None:
        """Buffer a single item and flush if the threshold is reached.

        Args:
            item: The item to enqueue in the internal buffer.
        """
        # Append the new item to the buffer
        self._buffer.append(item)

        # Flush immediately if the buffer reached the threshold
        if len(self._buffer) >= self.threshold and self.auto_flush :
            self.flush()

    def handle_many(self, items: Iterable[T]) -> None:
        """Buffer multiple items, flushing as thresholds are crossed.

        Args:
            items: An iterable of items to enqueue in order.
        """
        # Enqueue each incoming item using the single-item path
        for it in items:
            self.handle(it)

    # def flush(self) -> None:
    #     """Persist the current buffer via the callback and clear it.

    #     If the buffer is empty, this method is a no-op.
    #     """
    #     # Skip work if there is nothing to persist
    #     if not self._buffer:
    #         return

    #     # Invoke the provided persistence callback with the buffered items
    #     self.save_callback(self._buffer)

    #     # Clear the buffer after a successful callback
    #     self._buffer.clear()

    def flush(self, uow: Uow | None = None) -> None:
        if not self._buffer:
            return
        if uow is None:
            with self.uow_factory() as local:
                self.save_callback(self._buffer, uow=local)
                local.commit()
        else:
            self.save_callback(self._buffer, uow=uow)
        self._buffer.clear()

    def finalize(self) -> None:
        """Flush any remaining items, typically at the end of processing.

        This is intended to be called once when no more items will arrive.
        """
        # Ensure no residual items are left unpersisted
        self.flush()
