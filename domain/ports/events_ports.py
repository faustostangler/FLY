# domain/ports.py
from typing import Protocol, Callable, Any

EventHandler = Callable[[Any], None]

class EventPublisherPort(Protocol):
    def publish(self, topic: str, event: Any) -> None: ...

class EventSubscriberPort(Protocol):
    def subscribe(self, topic: str, handler: EventHandler) -> None: ...
