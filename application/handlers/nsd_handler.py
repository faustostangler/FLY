# application/handlers/nsd_handler.py
from domain.events.events import NSDReady
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.company_data_dto import CompanyDataDTO
from infrastructure.utils.list_flatenner import ListFlattener

class NsdReadyHandler:
    def __init__(self, scraper, nsd_repo, company_repo, outbox_repo, id_gen, clock):
        self.scraper = scraper
        self.nsd_repo = nsd_repo
        self.company_repo = company_repo
        self.outbox = outbox_repo
        self.id_gen = id_gen
        self.clock = clock

    def __call__(self, event: NSDReady) -> None:
        existing_nsd = [code for (code,) in self.nsd_repo.iter_existing_by_columns("nsd")]
        fetched = self.scraper.fetch_new_since(event.version_hash)
        dtos = [NsdDTO(**row) for row in ListFlattener.flatten(fetched)]
        names = {dto.company_name for dto in dtos}
        existing_companies = {name for (name,) in self.company_repo.iter_existing_by_columns("company_name")}
        missing = names - existing_companies
        if missing:
            to_create = [CompanyDataDTO(cvm_code=self.id_gen.create_id(size=6), company_name=name) for name in missing]
            self.company_repo.save_all(to_create)
        self.nsd_repo.save_all(dtos)
        # opcional: publicar StatementsFetched aqui, na outbox, se fizer sentido

# função adaptadora para ser usada no bus sem ter que reter instância global
def on_nsd_ready(evt: NSDReady, uow_factory, deps_factory) -> None:
    with uow_factory() as uow:
        handler = deps_factory.build_nsd_read_
