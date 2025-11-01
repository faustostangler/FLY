from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from domain.dtos import RatiosCacheEntryDTO
from domain.ports.ratios_cache_port import RatiosCachePort


class RatiosCacheAdapter(RatiosCachePort):
    """SQLite-backed cache storing ratios as parquet files."""

    TABLE_NAME = "cache"

    def __init__(
        self,
        *,
        base_dir: Path,
        max_cache_size_bytes: int = 1_000_000_000,
        max_age_days: int = 30,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir = self._base_dir
        self._db_path = self._base_dir / "fly_cache.db"
        self._max_cache_size_bytes = max_cache_size_bytes
        self._max_age = timedelta(days=max_age_days)

    def initialize(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    cache_key TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    code_hash TEXT NOT NULL
                )
                """
            )
            try:
                cursor.execute(
                    f"ALTER TABLE {self.TABLE_NAME} ADD COLUMN code_hash TEXT"
                )
            except sqlite3.OperationalError:
                pass
            conn.commit()

    def load(self, cache_key: str) -> tuple[pd.DataFrame, RatiosCacheEntryDTO] | None:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT file_path, size_bytes, created_at, accessed_at, access_count, code_hash FROM {self.TABLE_NAME} WHERE cache_key = ?",
                (cache_key,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            file_path = Path(row[0])
            if not file_path.exists():
                cursor.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE cache_key = ?",
                    (cache_key,),
                )
                conn.commit()
                return None

            try:
                df = pd.read_parquet(file_path)
            except Exception:
                file_path.unlink(missing_ok=True)
                cursor.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE cache_key = ?",
                    (cache_key,),
                )
                conn.commit()
                return None

            accessed_at = datetime.now()
            cursor.execute(
                f"UPDATE {self.TABLE_NAME} SET accessed_at = ?, access_count = access_count + 1 WHERE cache_key = ?",
                (accessed_at.isoformat(), cache_key),
            )
            conn.commit()

            entry = RatiosCacheEntryDTO(
                cache_key=cache_key,
                file_path=str(file_path),
                size_bytes=row[1],
                created_at=datetime.fromisoformat(row[2]),
                accessed_at=accessed_at,
                access_count=row[4] + 1,
                code_hash=row[5],
            )
            return df, entry

    def store(self, cache_key: str, df: pd.DataFrame, code_hash: str) -> RatiosCacheEntryDTO:
        file_path = self._cache_dir / f"{cache_key}.parquet"
        df.to_parquet(file_path, compression="zstd")
        size_bytes = file_path.stat().st_size
        now = datetime.now()

        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.TABLE_NAME} (cache_key, file_path, size_bytes, created_at, accessed_at, access_count, code_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    file_path=excluded.file_path,
                    size_bytes=excluded.size_bytes,
                    created_at=excluded.created_at,
                    accessed_at=excluded.accessed_at,
                    access_count=excluded.access_count,
                    code_hash=excluded.code_hash
                """,
                (
                    cache_key,
                    str(file_path),
                    size_bytes,
                    now.isoformat(),
                    now.isoformat(),
                    1,
                    code_hash,
                ),
            )
            conn.commit()
            self._evict_cache_if_needed(conn)

        return RatiosCacheEntryDTO(
            cache_key=cache_key,
            file_path=str(file_path),
            size_bytes=size_bytes,
            created_at=now,
            accessed_at=now,
            access_count=1,
            code_hash=code_hash,
        )

    def invalidate_outdated(self, *, code_hash: str) -> None:
        cutoff = datetime.now() - self._max_age
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT cache_key, file_path, code_hash, accessed_at FROM {self.TABLE_NAME}"
            )
            rows = cursor.fetchall()
            for cache_key, file_path, stored_hash, accessed_at in rows:
                remove = stored_hash != code_hash
                if not remove:
                    try:
                        last_access = datetime.fromisoformat(accessed_at)
                    except Exception:
                        last_access = datetime.min
                    remove = last_access < cutoff
                if remove:
                    Path(file_path).unlink(missing_ok=True)
                    cursor.execute(
                        f"DELETE FROM {self.TABLE_NAME} WHERE cache_key = ?",
                        (cache_key,),
                    )
            conn.commit()
            self._evict_cache_if_needed(conn)

    def _evict_cache_if_needed(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()
        cursor.execute(f"SELECT SUM(size_bytes) FROM {self.TABLE_NAME}")
        total_size = cursor.fetchone()[0] or 0
        while total_size > self._max_cache_size_bytes:
            cursor.execute(
                f"""
                SELECT cache_key, file_path, size_bytes
                FROM {self.TABLE_NAME}
                ORDER BY access_count ASC, created_at ASC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if not row:
                break
            cache_key, file_path, size_bytes = row
            Path(file_path).unlink(missing_ok=True)
            cursor.execute(
                f"DELETE FROM {self.TABLE_NAME} WHERE cache_key = ?",
                (cache_key,),
            )
            conn.commit()
            total_size -= size_bytes or 0
