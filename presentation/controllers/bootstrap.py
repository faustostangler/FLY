# presentation/controllers/bootstrap.py
from infrastructure.db.sqlalchemy import build_engine, build_session_factory
from infrastructure.messaging.events_messaging import InMemoryEventBus
from infrastructure.repositories.outbox_repository import SqlAlchemyOutboxRepository
from infrastructure.utils.worker_dispatcher import OutboxDispatcherWorker
from infrastructure.utils.clock import UtcClock
from infrastructure.utils.id_generator import IdGenerator

from application.handlers.nsd_handler import on_nsd_ready
from infrastructure.factories.cli_factory import cli_factory  # existente, para montar scrapers/repos
from infrastructure.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork

# engine + sessions
_engine = build_engine("sqlite:///fly.sqlite3")
_session_factory = build_session_factory(_engine)

# bus em memória
_event_bus = InMemoryEventBus()

# factories
def uow_factory():
    return SqlAlchemyUnitOfWork(_session_factory)

def outbox_repo_factory(session):
    return SqlAlchemyOutboxRepository(session)

# fábrica de dependências para handlers (fecha sobre scrapers/repos do mesmo Session)
class HandlerDepsFactory:
    def __init__(self, id_gen, clock):
        self.id_gen = id_gen
        self.clock = clock

    def build_nsd_ready_handler(self, uow):
        # reaproveite as factories existentes mas injetando a mesma Session da UoW
        # se suas factories atuais não aceitam Session, crie variações “*_with_session”
        from infrastructure.scrapers.nsd_scraper import NsdScraper
        from infrastructure.repositories.nsd_repository import RepositoryNsd
        from infrastructure.repositories.company_data_repository import RepositoryCompanyData
        from infrastructure.repositories.outbox_repository import SqlAlchemyOutboxRepository
        from application.handlers.nsd_handler import NsdReadyHandler

        return NsdReadyHandler(
            scraper=NsdScraper(),
            nsd_repo=RepositoryNsd(uow.session),
            company_repo=RepositoryCompanyData(uow.session),
            outbox_repo=SqlAlchemyOutboxRepository(uow.session),
            id_gen=self.id_gen,
            clock=self.clock,
        )

_deps_factory = HandlerDepsFactory(id_gen=IdGenerator(), clock=UtcClock())

# inscrição do handler
_event_bus.subscribe("NSDReady", lambda evt: on_nsd_ready(evt, uow_factory, _deps_factory))

# worker da outbox
_dispatcher = OutboxDispatcherWorker(_session_factory, outbox_repo_factory, event_bus=_event_bus, batch_size=100, idle_sleep=0.3)
_dispatcher.start()

# a CLI pode seguir chamando o caso de uso como já faz
from __future__ import annotations

"""Optional bootstrap for event-driven wiring.

This module provides minimal wiring for an in-memory event bus and an outbox
dispatcher worker using the existing infrastructure components. It intentionally
avoids coupling to application-specific handlers or scrapers to prevent import
errors during static analysis when those components evolve.
"""

from infrastructure.adapters.engine_setup import EngineSetup
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.messaging.events_messaging import InMemoryEventBus
from infrastructure.repositories.outbox_repository import SqlAlchemyOutboxRepository
from infrastructure.utils.uow import SqlAlchemyUnitOfWork
from infrastructure.utils.worker_dispatcher import OutboxDispatcherWorker

# Initialize configuration and logger
_config = ConfigAdapter()
_logger = Logger(_config)

# Build engine/session factory via EngineSetup helper
_engine_setup = EngineSetup(_config.database.connection_string, _logger)
_session_factory = _engine_setup.Session

# In-memory event bus (other modules may import and subscribe as needed)
event_bus = InMemoryEventBus()


def uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session_factory)


def outbox_repo_factory(session) -> SqlAlchemyOutboxRepository:
    return SqlAlchemyOutboxRepository(session)


# Outbox dispatcher worker (can be started by the application entrypoint if desired)
outbox_dispatcher = OutboxDispatcherWorker(
    _session_factory, outbox_repo_factory, event_bus=event_bus, batch_size=100, idle_sleep=0.3
)
