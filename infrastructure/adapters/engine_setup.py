from __future__ import annotations

from typing import Type

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from application.ports.logger_port import LoggerPort
from infrastructure.models import BaseModel


class EngineSetup:
    """Reusable mixin for adapters that need SQLAlchemy engine setup."""

    def __init__(
        self,
        connection_string: str,
        logger: LoggerPort | None,
        *,
        base: Type[DeclarativeBase] | None = None,
        metadata: MetaData | None = None,
        create_schema: bool | None = None,
    ) -> None:
        """Initialize engine, session factory and schema.

        Args:
            connection_string: Connection string for the target database.
            logger: Logger adapter for emitting lifecycle messages.
            base: Declarative base that owns the metadata for schema creation.
                When provided it takes precedence over ``metadata``.
            metadata: SQLAlchemy metadata to use when creating tables. Defaults
                to the project's base model metadata. Retained for backwards
                compatibility.
            create_schema: Controls whether ``metadata.create_all`` runs during
                initialization. ``None`` preserves the previous behaviour,
                creating the schema eagerly.
        """

        self.logger = logger
        self._base: Type[DeclarativeBase] = base or BaseModel
        self._metadata = metadata or self._base.metadata
        self._schema_requested = True if create_schema is None else create_schema

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
        if self._schema_requested:
            self.create_schema()

        # self.logger.log(f"Create Instance Base Class {self.__class__.__name__}", level="info")

    def create_schema(self) -> None:
        """Materialize the schema for the configured metadata."""

        self._metadata.create_all(self.engine)

