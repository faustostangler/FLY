# sqlalchemy_engine_mixin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from infrastructure.config import Config
from domain.ports import LoggerPort
from infrastructure.models.base_model import BaseModel

class SqlAlchemyEngineMixin:
    """Reusable mixin for adapters that need SQLAlchemy engine + session setup."""
    def __init__(self, config: Config, logger: LoggerPort) -> None:
        """Initialize the repository infrastructure: engine, session, and schema.

        This constructor sets up the SQLite engine with threading support,
        configures the session factory for ORM transactions, and ensures
        that all declared models are created in the database.

        Args:
            config (Config): Application configuration containing the database connection string.
            logger (LoggerPort): Logger used for emitting repository lifecycle messages.
        """
        # Store configuration and logger for use throughout the repository
        self.config = config
        self.logger = logger

        # Create SQLAlchemy engine for SQLite with thread-safe settings
        self.engine = create_engine(
            config.database.connection_string,
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
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.execute(text("PRAGMA cache_size=-65536"))  # 64 MB

        # Create a session factory for managing DB transactions
        self.Session = sessionmaker(
            bind=self.engine,
            autoflush=True,
            expire_on_commit=True,
        )

        # Automatically create all tables defined in the SQLAlchemy models
        BaseModel.metadata.create_all(self.engine)

        # self.logger.log(f"Create Instance Base Class {self.__class__.__name__}", level="info")

    def _init_engine(self, config, logger):
        # Initialize SQLAlchemy engine here
        pass
