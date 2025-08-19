from application.mappers import CompanyDataMapper
from domain.ports import AffinityHttpClientPort, ConfigPort, LoggerPort
from infrastructure.factories import datacleaner_factory
from infrastructure.repositories import CompanyDataRepository
from infrastructure.scrapers import CompanyDataScraper
from infrastructure.utils import MetricsCollector, WorkerPool
from presentation.controllers import Cli


def cli_factory(config: ConfigPort, logger: LoggerPort) -> Cli:
    datacleaner = datacleaner_factory(config, logger)
    mapper = CompanyDataMapper(datacleaner)
    metrics_collector = MetricsCollector()
    worker_pool = WorkerPool(config, metrics_collector, config.worker_pool.max_workers)
    company_repository = CompanyDataRepository(config=config, logger=logger)
    company_scraper = CompanyDataScraper(
        config=config,
        logger=logger,
        datacleaner=datacleaner,
        mapper=mapper,
        metrics_collector=metrics_collector,
        worker_pool=worker_pool,
        http_client=AffinityHttpClientPort,
    )
    # company_scraper: CompanyDataScraperPort


    # worker_pool = WorkerPool(config, metrics_collector=collector, ...)
    # ...
    # return Cli(
    #     config=config,
    #     logger=logger,
    #     data_cleaner=data_cleaner,
    #     metrics_collector=collector,
    #     company_repo=company_repo,
    #     ...
    # )
    return Cli(
        config=config,
        logger=logger,
        datacleaner=datacleaner,
        metrics_collector= metrics_collector,
        worker_pool=worker_pool,
        company_repository=company_repository,
        company_scraper=company_scraper,
    )
