from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from domain.dtos.ratios_cache_entry_dto import RatiosCacheEntryDTO
from domain.ports.ratios_cache_port import RatiosCachePort
from infrastructure.config.cache import CacheConfig, load_cache_config
from domain.dtos.ratios_cache_context_dto import RatiosCacheContextDTO
from infrastructure.models.ratios_cache_model import (
    RatiosCacheBase,
    RatiosCacheEntryModel,
)


class RatiosCacheAdapter(RatiosCachePort):
    """SQLAlchemy-backed cache storing ratios as parquet files."""

    def __init__(self, *, config: CacheConfig | None = None) -> None:
        self._config = config or load_cache_config()
        self._base_dir = Path(self._config.base_dir)
# =======
#     TABLE_NAME = "cache"

#     def __init__(
#         self,
#         *,
#         base_dir: Path,
#         max_cache_size_bytes: int = 1_000_000_000, # create a config entry for cache size and age
#         max_age_days: int = 30,
#     ) -> None:
#         self._base_dir = Path(base_dir)
#         self._base_dir.mkdir(parents=True, exist_ok=True)
# >>>>>>> Stashed changes
        self._cache_dir = self._base_dir
        self._max_cache_size_bytes = self._config.max_cache_size_bytes
        self._max_age = self._config.max_age
        self._parquet_compression = self._config.parquet_compression

        if RatiosCacheEntryModel.__tablename__ != self._config.table_name:
            RatiosCacheEntryModel.__tablename__ = self._config.table_name
            table = getattr(RatiosCacheEntryModel, "__table__", None)
            if table is not None:
                table.name = self._config.table_name

        self._engine = create_engine(
            self._config.connection_string,
            connect_args={"check_same_thread": False, "timeout": 60},
            pool_pre_ping=True,
            future=True,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            future=True,
        )

    def initialize(self) -> None:
        RatiosCacheBase.metadata.create_all(self._engine)

    def load(self, cache_key: str) -> tuple[pd.DataFrame, RatiosCacheEntryDTO] | None:
        with self._session_factory() as session:
            entry = session.get(RatiosCacheEntryModel, cache_key)
            if entry is None:
                return None

            file_path = Path(entry.file_path)
            if not file_path.exists():
                self._remove_entry(session, entry)
                return None

            try:
                df = pd.read_parquet(file_path)
            except Exception:
                file_path.unlink(missing_ok=True)
                self._remove_entry(session, entry)
                return None

            entry.accessed_at = datetime.now()
            entry.access_count += 1
            session.add(entry)  # garante que será persistido

            return df, entry.to_dto()

    def store(
        self,
        *,
        context: RatiosCacheContextDTO,
        df: pd.DataFrame,
        company_name: str,
    ) -> RatiosCacheEntryDTO:
        file_path = self._build_file_path(context=context, company_name=company_name)
        temp_path = file_path.with_suffix(".tmp")

        df.to_parquet(temp_path, compression=self._parquet_compression)
        with temp_path.open("rb+") as handle:
            handle.flush()
            os.fsync(handle.fileno())

        size_bytes = temp_path.stat().st_size
        now = datetime.now()

        entry: RatiosCacheEntryModel | None = None

        try:
            with self._session_factory.begin() as session:
                entry = session.get(RatiosCacheEntryModel, context.cache_key)
                if entry is None:
                    entry = RatiosCacheEntryModel(
                        cache_key=context.cache_key,
                        file_path=str(file_path),
                        size_bytes=size_bytes,
                        created_at=now,
                        accessed_at=now,
                        access_count=1,
                        code_hash=context.code_hash,
                    )
                    session.add(entry)
                else:
                    entry.file_path = str(file_path)
                    entry.size_bytes = size_bytes
                    entry.created_at = now
                    entry.accessed_at = now
                    entry.access_count = 1
                    entry.code_hash = context.code_hash
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.replace(file_path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            with self._session_factory.begin() as session:
                stale_entry = session.get(RatiosCacheEntryModel, context.cache_key)
                if stale_entry is not None:
                    session.delete(stale_entry)
            raise

        if entry is None:
            # Defensive guard: SQLAlchemy guarantees assignment above but satisfy type checkers.
            raise RuntimeError(
                "Failed to persist cache metadata for key '%s'" % context.cache_key
            )

        entry_dto = entry.to_dto()
        self._invalidate_outdated(code_hash=context.code_hash)
        self._evict_cache_if_needed()
        return entry_dto

    def invalidate_outdated(self, *, code_hash: str) -> None:
        self._invalidate_outdated(code_hash=code_hash)
        self._evict_cache_if_needed()

    def _invalidate_outdated(self, *, code_hash: str) -> None:
        cutoff = datetime.now() - self._max_age

        with self._session_factory.begin() as session:
            entries = session.scalars(
                select(RatiosCacheEntryModel).where(
                    (RatiosCacheEntryModel.code_hash != code_hash)
                    | (RatiosCacheEntryModel.accessed_at < cutoff)
                )
            ).all()

            for entry in entries:
                Path(entry.file_path).unlink(missing_ok=True)
                session.delete(entry)

    def _evict_cache_if_needed(self) -> None:
        with self._session_factory.begin() as session:
            total_size = session.execute(
                select(func.coalesce(func.sum(RatiosCacheEntryModel.size_bytes), 0))
            ).scalar_one()

            if total_size <= self._max_cache_size_bytes:
                return

            entries = session.scalars(
                select(RatiosCacheEntryModel)
                .order_by(
                    RatiosCacheEntryModel.access_count.asc(),
                    RatiosCacheEntryModel.created_at.asc(),
                )
            )

            for entry in entries:
                if total_size <= self._max_cache_size_bytes:
                    break

                Path(entry.file_path).unlink(missing_ok=True)
                total_size -= entry.size_bytes
                session.delete(entry)

    def _remove_entry(self, session: Session, entry: RatiosCacheEntryModel) -> None:
        session.delete(entry)

    def _build_file_path(
        self,
        *,
        context: RatiosCacheContextDTO,
        company_name: str,
    ) -> Path:
        safe_company = self._sanitize_company_name(company_name)
        version_segment = f"v{context.version}"
        target_dir = self._cache_dir / context.logical_name / version_segment / safe_company
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / f"{context.cache_key}.parquet"

    def _sanitize_company_name(self, company_name: str) -> str:
        normalized = unicodedata.normalize("NFKD", company_name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        cleaned = re.sub(r"[^A-Za-z0-9]+", "-", ascii_name).strip("-")
        if not cleaned:
            cleaned = "unknown"
        return cleaned[:120]
