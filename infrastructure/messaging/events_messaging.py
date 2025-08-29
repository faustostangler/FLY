# infrastructure/messaging/inmemory_bus.py
import threading
from typing import Dict, List, Callable, Any
from domain.ports.events_ports import EventPublisherPort, EventSubscriberPort
import logging
class InMemoryEventBus(EventPublisherPort, EventSubscriberPort):
    def __init__(self):
        self._subs: Dict[str, List[Callable[[Any], None]]] = {}
        self._lock = threading.Lock()
        self._log = logging.Logger("InMemoryEventBus", level=logging.INFO)

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        with self._lock:
            self._subs.setdefault(topic, []).append(handler)
        if self._log:
            self._log.info(
                "eventbus.subscription",
                extra={"topic": topic, "handler": self._handler_name(handler)}
            )

    def publish(self, topic: str, event: Any) -> None:
        with self._lock:
            handlers = list(self._subs.get(topic, []))
        if self._log:
            self._log.info(
                "eventbus.dispatch.start",
                extra={
                    "topic": topic,
                    "event_type": event.__class__.__name__,
                    "handlers": len(handlers),
                    "correlation_id": getattr(event, "correlation_id", None),
                },
            )
        for h in handlers:
            h(event)  # exceções sobem; o dispatcher marca failed
