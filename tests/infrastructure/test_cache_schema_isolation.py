from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import sys

import pytest
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

pytest.importorskip("pandas")

from infrastructure.cache.ratios_cache import CacheRatiosAdapter
from infrastructure.repositories.repository_company_data import RepositoryCompanyData
from infrastructure.uow.uow import UowFactory


class DummyLogger:
    def log(self, message, level="info", progress=None, extra=None, worker_id=None, show_path=None):  # noqa: D401
        """Minimal logger stub used in tests."""


@dataclass
class DummyPaths:
    data_dir: Path
    cache_dir: Path
    temp_dir: Path
    log_dir: Path
    root_dir: Path


class DummyCacheConfig:
    def __init__(self) -> None:
        self._max_age = timedelta(days=30)

    @property
    def max_cache_size_bytes(self) -> int:
        return 10_000_000

    @property
    def max_age_days(self) -> int:
        return 30

    @property
    def max_age(self) -> timedelta:
        return self._max_age

    @property
    def parquet_compression(self) -> str:
        return "snappy"


class DummyRepositoryConfig:
    @property
    def batch_size(self) -> int:
        return 50

    @property
    def persistence_threshold(self) -> int:
        return 1


class DummyDatabaseConfig:
    def __init__(self, *, data_dir: Path, db_filename: str, cache_filename: str) -> None:
        self._data_dir = data_dir
        self.db_filename = db_filename
        self.db_cache_filename = cache_filename
        self.tables = {}

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @property
    def connection_string(self) -> str:
        return f"sqlite:///{(self._data_dir / self.db_filename).as_posix()}"

    @property
    def connection_cache_string(self) -> str:
        return f"sqlite:///{(self._data_dir / self.db_cache_filename).as_posix()}"


class DummyConfig:
    def __init__(self, *, data_dir: Path, cache_dir: Path) -> None:
        db_filename = "fly.db"
        cache_filename = "flycache.db"
        self.paths = DummyPaths(
            data_dir=data_dir,
            cache_dir=cache_dir,
            temp_dir=cache_dir / "tmp",
            log_dir=data_dir / "logs",
            root_dir=data_dir,
        )
        self.paths.temp_dir.mkdir(parents=True, exist_ok=True)
        self.paths.log_dir.mkdir(parents=True, exist_ok=True)
        self.database = DummyDatabaseConfig(
            data_dir=data_dir,
            db_filename=db_filename,
            cache_filename=cache_filename,
        )
        self.cache = DummyCacheConfig()
        self.repository = DummyRepositoryConfig()


def _user_tables(db_path: Path) -> set[str]:
    from sqlalchemy import create_engine

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        return {name for (name,) in rows if not name.startswith("sqlite_")}
    finally:
        engine.dispose()


def test_cache_adapter_creates_only_cache_table(tmp_path) -> None:
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    data_dir.mkdir()
    cache_dir.mkdir()

    config = DummyConfig(data_dir=data_dir, cache_dir=cache_dir)
    logger = DummyLogger()

    adapter = CacheRatiosAdapter(config=config, logger=logger)
    adapter.initialize()

    cache_tables = _user_tables(data_dir / config.database.db_cache_filename)
    assert cache_tables == {"tbl_cache"}


def test_domain_repository_does_not_see_cache_table(tmp_path) -> None:
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    data_dir.mkdir()
    cache_dir.mkdir()

    config = DummyConfig(data_dir=data_dir, cache_dir=cache_dir)
    logger = DummyLogger()

    repository = RepositoryCompanyData(config=config, logger=logger)
    uow_factory = UowFactory(session_factory=repository.Session)

    # trigger schema creation explicitly to mirror production bootstrap
    with uow_factory() as uow:
        _ = repository.get_model_class()

    main_tables = _user_tables(data_dir / config.database.db_filename)
    assert "tbl_cache" not in main_tables
    assert "tbl_company" in main_tables
