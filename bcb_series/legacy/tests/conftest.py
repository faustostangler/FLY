import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def SessionLocal(engine):
    Session = sessionmaker(bind=engine)
    return Session


class DummyLogger:
    def log(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


class DummyConfig:
    class Database:
        connection_string = "sqlite:///:memory:"

    database = Database()

    class Global:
        app_name = "TEST"
        max_workers = 1
        queue_size = 10
        threshold = 10
        batch_size = 100
        request_timeout_sec = 5.0
        user_agent = "test-agent"
        retries = 1

    global_settings = Global()

    class Transformers:
        math_target_accounts = ("01",)
        _enabled = {"math": True}
        _order = ("math",)

        @property
        def enabled(self):
            return self._enabled

        @property
        def order(self):
            return self._order

    transformers = Transformers()

    class Domain:
        statements_types = ("dre",)
        words_to_remove = ()
        base_currency = "BRL"
        nsd_gap_days = 0

    domain = Domain()
