# application/handlers/nsd_handler.py
from __future__ import annotations
from typing import TYPE_CHECKING, Iterable

from domain.events.events import NSDReady
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.company_data_dto import CompanyDataDTO
from infrastructure.utils.list_flatenner import ListFlattener

if TYPE_CHECKING:
    from infrastructure.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
    from infrastructure.repositories.nsd_repository import RepositoryNsd
    from infrastructure.repositories.company_data_repository import RepositoryCompanyData
    from infrastructure.repositories.outbox_repository import SqlAlchemyOutboxRepository
    from infrastructure.scrapers.nsd_scraper import NsdScraper
    from infrastructure.utils.id_generator import IdGenerator
    from infrastructure.utils.clock import UtcClock


class NsdReadyHandler:
    """
    Handles the NSDReady event by processing NSD data and creating
    missing company records.

    This handler operates within a Unit of Work to ensure transactional
    integrity for all database operations.
    """

    def __init__(
        self,
        scraper: NsdScraper,
        nsd_repo: RepositoryNsd,
        company_repo: RepositoryCompanyData,
        outbox_repo: SqlAlchemyOutboxRepository,
        id_gen: IdGenerator,
        clock: UtcClock,
    ):
        """Initializes the handler with all necessary dependencies."""
        self.scraper = scraper
        self.nsd_repo = nsd_repo
        self.company_repo = company_repo
        self.outbox = outbox_repo
        self.id_gen = id_gen
        self.clock = clock

    def __call__(self, event: NSDReady) -> None:
        """
        Executes the business logic for the NSDReady event.

        Args:
            event (NSDReady): The event payload containing the version hash.
        """
        # Step 1: Fetch new NSD data since the last version
        # The scraper returns a generator or list of dictionaries
        fetched_data = self.scraper.fetch_new_since(event.version_hash)
        
        # Flatten the data into a single list of dictionaries
        dtos_data: Iterable[dict] = ListFlattener.flatten(fetched_data)
        
        # Convert raw dictionaries to NsdDTO objects
        nsd_dtos = [NsdDTO(**row) for row in dtos_data]

        # Step 2: Identify and create missing companies
        # Get all unique company names from the new NSD data
        new_company_names = {dto.company_name for dto in nsd_dtos}
        
        # Get existing company names from the repository
        existing_companies = {
            name for (name,) in self.company_repo.iter_existing_by_columns("company_name")
        }
        
        # Find names that exist in the new data but not in the database
        missing_names = new_company_names - existing_companies
        
        if missing_names:
            # Create new CompanyDataDTOs for the missing companies
            companies_to_create = [
                CompanyDataDTO(
                    cvm_code=self.id_gen.create_id(size=6), company_name=name
                )
                for name in missing_names
            ]
            
            # Save the new companies to the repository
            self.company_repo.save_all(companies_to_create)

        # Step 3: Save all new NSD entries
        self.nsd_repo.save_all(nsd_dtos)

        # Optional Step: Publish a downstream event
        # If the statements need to be fetched after NSD and companies are saved,
        # an event can be published to the outbox. For example:
        # statement_event = StatementsFetched(version=event.version_hash, ...)
        # self.outbox.add(statement_event)


def on_nsd_ready(
    evt: NSDReady,
    uow_factory: callable,
    deps_factory: callable,
) -> None:
    """
    Adapter function to execute the handler logic within a transactional
    Unit of Work (UoW) context.

    This function is the entry point for the event bus. It creates a UoW,
    builds the handler with the UoW's session, and then calls the handler.
    If any operation within the handler fails, the UoW will roll back.
    """
    with uow_factory() as uow:
        # Build the handler with the Unit of Work to ensure all
        # repositories share the same session.
        handler = deps_factory.build_nsd_ready_handler(uow)
        handler(evt)
        # The UoW context manager automatically commits on success
        # and rolls back on error.
