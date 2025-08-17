"""Persistent cache for HTTP responses keyed by URL."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from .base_model import BaseModel


class HttpCacheModel(BaseModel):
    """Store metadata and body for conditional HTTP requests."""

    __tablename__ = "http_cache"

    url: Mapped[str] = mapped_column(String(1024), primary_key=True)
    etag: Mapped[str | None] = mapped_column(String(256))
    last_modified: Mapped[str | None] = mapped_column(String(256))
    body: Mapped[bytes | None] = mapped_column(LargeBinary)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Index("ix_http_cache_url", HttpCacheModel.url)
