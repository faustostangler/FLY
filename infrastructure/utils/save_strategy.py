from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Iterable, List, Optional, TypeVar

from domain.ports.logger_port import ConfigPort

T = TypeVar("T")

@dataclass
class SaveStrategy(Generic[T]):
    save_callback: Callable[[List[T]], None]
    threshold: int
    _buffer: List[T] = field(default_factory=list)

    @classmethod
    def from_config(
        cls,
        save_callback: Optional[Callable[[List[T]], None]] = None,
        threshold: Optional[int] = None,
        config: Optional[ConfigPort] = None,
    ) -> "SaveStrategy[T]":
        cb = save_callback or (lambda _: None)
        th = threshold or (config.repository.persistance_threshold if config else 50)
        return cls(cb, th)

    def handle(self, item: T) -> None:
        self._buffer.append(item)
        if len(self._buffer) >= self.threshold:
            self.flush()

    def handle_many(self, items: Iterable[T]) -> None:
        for it in items:
            self.handle(it)

    def flush(self) -> None:
        if not self._buffer:
            return
        self.save_callback(self._buffer)
        self._buffer.clear()

    def finalize(self) -> None:
        self.flush()
