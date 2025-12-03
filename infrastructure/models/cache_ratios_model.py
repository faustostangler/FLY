from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from domain.dtos.cache_ratios_entry_dto import CacheRatiosEntryDTO


class CacheBase(DeclarativeBase):
    """Declarative base dedicated to cache-related ORM models."""
    pass

class CacheEntry(CacheBase):
    """ORM model representing cached ratios metadata."""

    __tablename__ = "tbl_cache"
    __table_args__ = (
        CheckConstraint("size_bytes >= 0", name="ck_cache_size_non_negative"),
        Index("ix_cache_access_count", "access_count"),
        Index("ix_cache_created_at", "created_at"),
        Index("ix_cache_accessed_at", "accessed_at"),
    )

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # chaves estáveis do cache. nomes genéricos, não amarrados a casos particulares
    # logical_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    # version: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    # checksum: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # # payload pode ser caminho para parquet ou blob. aqui deixo ambos opcionados
    # payload_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # payload_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    # created_at: Mapped[str] = mapped_column(String(26), nullable=False, default=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    # is_current: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1/0 para SQLite simples


    def to_dto(self) -> CacheRatiosEntryDTO:
        return CacheRatiosEntryDTO(
            cache_key=self.cache_key,
            file_path=self.file_path,
            size_bytes=self.size_bytes,
            created_at=self.created_at,
            accessed_at=self.accessed_at,
            access_count=self.access_count,
            code_hash=self.code_hash,
        )
