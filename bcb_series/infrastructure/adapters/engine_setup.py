from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from application.ports.logger_port import LoggerPort
from infrastructure.models import BaseModel


class EngineSetup():
    """Reusable mixin for adapters that need SQLAlchemy engine setup."""

    def __init__(
        self,
        connection_string: str,
        logger: LoggerPort | None,
        *,
        # metadata: MetaData | None = None,
        orm_base: type[DeclarativeBase] | None = None,
        create_schema: bool = True,
    ) -> None:
        """Initialize engine, session factory and schema.

        Args:
            connection_string: Connection string for the target database.
            logger: Logger adapter for emitting lifecycle messages.
            metadata: SQLAlchemy metadata to use when creating tables. Defaults
                to the project's base model metadata.
        """

        self.logger = logger
        # self._metadata = metadata or BaseModel.metadata

        # Create SQLAlchemy engine for SQLite with thread-safe settings
        self.engine = create_engine(
            connection_string,
            connect_args={
                "check_same_thread": False,
                "timeout": 60,
            },  # allow usage from multiple threads
            pool_pre_ping=True,
            future=True,
        )

        # Enable Write-Ahead Logging mode to support concurrent reads/writes
        with self.engine.connect() as conn:
            # conn.execute(text("PRAGMA optimize"))
            # conn.execute(text("PRAGMA synchronous=FULL"))
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA busy_timeout=60000;"))
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
        # cria apenas as tabelas pertencentes à base recebida
        if create_schema:
            base = orm_base or BaseModel          # <- fallback somente aqui
            base.metadata.create_all(self.engine) # <- cria só o metadata passado

        # self._metadata.create_all(self.engine)

        # self.logger.log(f"Create Instance Base Class {self.__class__.__name__}", level="info")
