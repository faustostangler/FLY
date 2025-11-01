from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from domain.dtos import RatiosCacheEntryDTO
from domain.ports.ratios_cache_port import RatiosCachePort
from infrastructure.config.cache import CacheConfig, load_cache_config
from infrastructure.models.ratios_cache_model import (
    RatiosCacheBase,
    RatiosCacheEntryModel,
)


class RatiosCacheAdapter(RatiosCachePort):
    """SQLAlchemy-backed cache storing ratios as parquet files."""

    def __init__(self, *, config: CacheConfig | None = None) -> None:
        self._config = config or load_cache_config()
        self._base_dir = Path(self._config.base_dir)
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

            with session.begin():
                entry.accessed_at = datetime.now()
                entry.access_count += 1

            return df, entry.to_dto()

    def store(self, cache_key: str, df: pd.DataFrame, code_hash: str) -> RatiosCacheEntryDTO:
        file_path = self._cache_dir / f"{cache_key}.parquet"
        temp_path = file_path.with_suffix(".parquet.tmp")

        df.to_parquet(temp_path, compression=self._parquet_compression)
        with temp_path.open("rb+") as handle:
            handle.flush()
            os.fsync(handle.fileno())

        size_bytes = temp_path.stat().st_size
        now = datetime.now()

        entry: RatiosCacheEntryModel | None = None

        try:
            with self._session_factory.begin() as session:
                entry = session.get(RatiosCacheEntryModel, cache_key)
                if entry is None:
                    entry = RatiosCacheEntryModel(
                        cache_key=cache_key,
                        file_path=str(file_path),
                        size_bytes=size_bytes,
                        created_at=now,
                        accessed_at=now,
                        access_count=1,
                        code_hash=code_hash,
                    )
                    session.add(entry)
                else:
                    entry.file_path = str(file_path)
                    entry.size_bytes = size_bytes
                    entry.created_at = now
                    entry.accessed_at = now
                    entry.access_count = 1
                    entry.code_hash = code_hash
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

        try:
            temp_path.replace(file_path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            with self._session_factory.begin() as session:
                stale_entry = session.get(RatiosCacheEntryModel, cache_key)
                if stale_entry is not None:
                    session.delete(stale_entry)
            raise

        if entry is None:
            # Defensive guard: SQLAlchemy guarantees assignment above but satisfy type checkers.
            raise RuntimeError("Failed to persist cache metadata for key '%s'" % cache_key)

        entry_dto = entry.to_dto()
        self._evict_cache_if_needed()
        return entry_dto

    def invalidate_outdated(self, *, code_hash: str) -> None:
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

        self._evict_cache_if_needed()

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
        with session.begin():
            session.delete(entry)
