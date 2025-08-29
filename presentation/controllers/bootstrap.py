# presentation/controllers/bootstrap.py

from __future__ import annotations

"""Bootstrap module to wire infrastructure and application services.

This module is responsible for initializing the application's core
dependencies, ensuring they are correctly configured and shared.
It follows a clear dependency injection pattern to build a consistent
service graph.
"""

from application.handlers.nsd_handler import on_nsd_ready
from infrastructure.adapters.engine_setup import EngineSetup
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.messaging.events_messaging import InMemoryEventBus
from infrastructure.repositories.outbox_repository import SqlAlchemyOutboxRepository
from infrastructure.repositories.company_data_repository import RepositoryCompanyData
from infrastructure.repositories.nsd_repository import RepositoryNsd
from infrastructure.scrapers.nsd_scraper import NsdScraper
from infrastructure.utils.clock import UtcClock
from infrastructure.utils.id_generator import IdGenerator
from infrastructure.utils.uow import SqlAlchemyUnitOfWork
from infrastructure.utils.worker_dispatcher import OutboxDispatcherWorker


# 1. Initialize core application components
_config = ConfigAdapter()
_logger = Logger(_config)

# 2. Setup database engine and session factory
_engine_setup = EngineSetup(_config.database.connection_string, _logger)
_session_factory = _engine_setup.Session


# 3. Define factories that use the shared session factory
# This ensures that all components built from these factories
# will be part of the same transaction context when used with a UoW.
def uow_factory() -> SqlAlchemyUnitOfWork:
    """Creates a new Unit of Work instance."""
    return SqlAlchemyUnitOfWork(_session_factory)

def outbox_repo_factory(session) -> SqlAlchemyOutboxRepository:
    """Creates an Outbox repository instance using a provided session."""
    return SqlAlchemyOutboxRepository(session)


# 4. Create a single factory for application-scoped dependencies
class ApplicationDepsFactory:
    """A factory to provide consistent, shared dependencies."""
    def __init__(self, config: ConfigAdapter, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.id_gen = IdGenerator(config=self.config, logger_name=self.config.fly_settings.app_name)
        self.clock = UtcClock()
        self.nsd_scraper = NsdScraper(config=self.config, logger=self.logger)


# 5. Initialize the core services and event bus
event_bus = InMemoryEventBus()
deps = ApplicationDepsFactory(config=_config, logger=_logger)


# 6. Subscribe the handler with its factories
# Note: The handler itself is not directly imported here to avoid circular dependencies
# but the on_nsd_ready function correctly receives the necessary factories.
# The `on_nsd_ready` function is the actual entry point, delegating to a UoW and a
# handler factory that uses the UoW's session.
event_bus.subscribe("NSDReady", lambda evt: on_nsd_ready(evt, uow_factory, deps))


# 7. Setup and start the outbox dispatcher worker
outbox_dispatcher = OutboxDispatcherWorker(
    _session_factory,
    outbox_repo_factory,
    event_bus=event_bus,
    batch_size=100,
    idle_sleep=0.3
)
outbox_dispatcher.start()

# For external use by the CLI or other entry points
__all__ = ["event_bus", "outbox_dispatcher", "uow_factory", "deps"]
