from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from domain.dto.worker_class_dto import WorkerTaskDTO


class RawStatementScraperPort(ABC):
    """Port for fetching raw statement HTML."""
    # def __init__(
    #     self,
    #     config: Config,
    #     logger: LoggerPort,
    # ) -> None:
    #     """Create the adapter with its configuration and logger."""
    #     self.config = config
    #     self.logger = logger

    #     # Create SQLAlchemy engine for SQLite with thread-safe settings
    #     self.engine = create_engine(
    #         config.database.connection_string,
    #         connect_args={
    #             "check_same_thread": False
    #         },  # allow usage from multiple threads
    #         future=True,
    #     )

    #     # Enable Write-Ahead Logging mode to support concurrent reads/writes
    #     with self.engine.connect() as conn:
    #         conn.execute(text("PRAGMA journal_mode=WAL"))
    #         conn.execute(text("PRAGMA foreign_keys=ON"))
    #         conn.execute(text("PRAGMA temp_store=MEMORY"))
    #         conn.execute(text("PRAGMA cache_size=-65536"))  # 64 MB

    #     # Create a session factory for managing DB transactions
    #     self.Session = sessionmaker(
    #         bind=self.engine,
    #         autoflush=True,
    #         expire_on_commit=True,
    #     )

    #     # Automatically create all tables defined in the SQLAlchemy models
    #     BaseModel.metadata.create_all(self.engine)

    #     # self.logger.log(f"Create Instance Base Class {self.__class__.__name__}", level="info")

    @abstractmethod
    def fetch(self, task: WorkerTaskDTO) -> dict[str, Any]:
        """Return statement rows for the given NSD wrapped in ``task``."""
        raise NotImplementedError
