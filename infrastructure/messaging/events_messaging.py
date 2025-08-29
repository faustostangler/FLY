# infrastructure/messaging/inmemory_bus.py
import threading
from typing import Dict, List, Callable, Any
from domain.ports.events_ports import EventPublisherPort, EventSubscriberPort

class InMemoryEventBus(EventPublisherPort, EventSubscriberPort):
    def __init__(self):
        self._subs: Dict[str, List[Callable[[Any], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        with self._lock:
            self._subs.setdefault(topic, []).append(handler)

    def publish(self, topic: str, event: Any) -> None:
        with self._lock:
            handlers = list(self._subs.get(topic, []))
        for h in handlers:
            h(event)  # exceções sobem; o dispatcher marca failed
