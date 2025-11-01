from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from domain.dtos import RatiosCacheEntryDTO


class RatiosCacheBase(DeclarativeBase):
    """Declarative base dedicated to cache-related ORM models."""


class RatiosCacheEntryModel(RatiosCacheBase):
    """ORM model representing cached ratios metadata."""

    __tablename__ = "cache"
    __table_args__ = (
        CheckConstraint("size_bytes >= 0", name="ck_cache_size_non_negative"),
        Index("ix_cache_access_count", "access_count"),
        Index("ix_cache_created_at", "created_at"),
        Index("ix_cache_accessed_at", "accessed_at"),
    )

    cache_key: Mapped[str] = mapped_column(String, primary_key=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    code_hash: Mapped[str] = mapped_column(String, nullable=False)

    def to_dto(self) -> RatiosCacheEntryDTO:
        return RatiosCacheEntryDTO(
            cache_key=self.cache_key,
            file_path=self.file_path,
            size_bytes=self.size_bytes,
            created_at=self.created_at,
            accessed_at=self.accessed_at,
            access_count=self.access_count,
            code_hash=self.code_hash,
        )
