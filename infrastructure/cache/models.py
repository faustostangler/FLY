from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from domain.dtos.cache_ratios_entry_dto import CacheRatiosEntryDTO


class CacheBase(DeclarativeBase):
    """Declarative base dedicated to cache persistence."""


class CacheEntryModel(CacheBase):
    """ORM mapping for cache entries stored in the dedicated database."""

    __tablename__ = "tbl_cache"
    __table_args__ = (
        UniqueConstraint(
            "logical_key",
            "version",
            "checksum",
            name="uq_cache_logical_version_checksum",
        ),
        CheckConstraint("size_bytes >= 0", name="ck_cache_size_non_negative"),
        CheckConstraint(
            "payload_path IS NOT NULL OR payload_blob IS NOT NULL",
            name="ck_cache_payload_present",
        ),
        Index("ix_cache_logical_key", "logical_key"),
        Index("ix_cache_version", "version"),
        Index("ix_cache_checksum", "checksum"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    logical_key: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    checksum: Mapped[str] = mapped_column(String, nullable=False)
    payload_path: Mapped[str | None] = mapped_column(String, nullable=True)
    payload_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    code_hash: Mapped[str] = mapped_column(String, nullable=False)

    def to_dto(self) -> CacheRatiosEntryDTO:
        file_path = self.payload_path or ""
        return CacheRatiosEntryDTO(
            cache_key=self.cache_key,
            file_path=file_path,
            size_bytes=self.size_bytes,
            created_at=self.created_at,
            accessed_at=self.accessed_at,
            access_count=self.access_count,
            code_hash=self.code_hash,
        )

    @staticmethod
    def payload_fields_from_entry(
        *,
        file_path: str | None,
        payload_blob: bytes | None,
    ) -> dict[str, Any]:
        """Normalize payload assignment for path/blob strategies."""

        return {
            "payload_path": file_path,
            "payload_blob": payload_blob,
        }
