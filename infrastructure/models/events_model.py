# infrastructure/events_model.py  (ajuste o caminho conforme seu projeto)
from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.models.base_model import BaseModel  # use o MESMO Base do restante do ORM

class OutboxEventModel(BaseModel):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("idx_outbox_status_available", "status", "available_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending|published|dead
