# sqlalchemy_engine_mixin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from domain.ports import LoggerPort
from infrastructure.models import BaseModel


class SqlAlchemyEngineMixin:
    """Reusable mixin for adapters that need SQLAlchemy engine setup."""

    def __init__(self, connection_string: str, logger: LoggerPort) -> None:
        """Initialize engine, session factory and schema.

        Args:
            connection_string: Connection string for the target database.
            logger: Logger adapter for emitting lifecycle messages.
        """
        self.logger = logger

        # Create SQLAlchemy engine for SQLite with thread-safe settings
        self.engine = create_engine(
            connection_string,
            connect_args={
                "check_same_thread": False
            },  # allow usage from multiple threads
            future=True,
        )

        # Enable Write-Ahead Logging mode to support concurrent reads/writes
        with self.engine.connect() as conn:
            # conn.execute(text("PRAGMA optimize"))
            # conn.execute(text("PRAGMA synchronous=FULL"))
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA busy_timeout=5000;"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.execute(text("PRAGMA cache_size=-65536"))  # 64 MB

        # Create a session factory for managing DB transactions
        self.Session = sessionmaker(
            bind=self.engine,
            autoflush=True,
            expire_on_commit=False,
            future=True,
        )

        # Automatically create all tables defined in the SQLAlchemy models
        BaseModel.metadata.create_all(self.engine)

        # self.logger.log(f"Create Instance Base Class {self.__class__.__name__}", level="info")
