# infrastructure/repositories/outbox_repository.py
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from infrastructure.models.events_model import OutboxEventModel

class SqlAlchemyOutboxRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, topic: str, event_obj: object, occurred_at: datetime) -> None:
        payload = json.dumps({"type": event_obj.__class__.__name__, "data": event_obj.__dict__}, default=str)
        row = OutboxEventModel(topic=topic, payload_json=payload, occurred_at=occurred_at)
        self._session.add(row)

    def fetch_available(self, limit: int = 50):
        q = (self._session.query(OutboxEventModel)
             .where(OutboxEventModel.status == "pending")
             .where(OutboxEventModel.available_at <= datetime.utcnow())
             .order_by(OutboxEventModel.id.asc())
             .limit(limit))
        return q.all()

    def mark_published(self, row: OutboxEventModel) -> None:
        row.status = "published"
        self._session.add(row)

    def mark_failed(self, row: OutboxEventModel, attempts_cap: int = 10) -> None:
        row.attempts += 1
        if row.attempts >= attempts_cap:
            row.status = "dead"
        else:
            delay = 2 ** min(row.attempts, 8)
            row.available_at = datetime.utcnow() + timedelta(seconds=delay)
        self._session.add(row)
