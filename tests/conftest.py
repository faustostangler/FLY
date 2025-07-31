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


class DummyConfig:
    class Database:
        connection_string = "sqlite:///:memory:"

    database = Database()

    class Global:
        app_name = "TEST"
        max_workers = 1
        queue_size = 10

    global_settings = Global()
