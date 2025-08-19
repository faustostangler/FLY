from __future__ import annotations

from application.mappers.company_data_mapper import CompanyDataMapper
from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort
from infrastructure.http.http_client import RequestsAffinityHttpClient
from infrastructure.repositories.company_data_repository import CompanyDataRepository
from infrastructure.scrapers.company_data_scraper import CompanyDataScraper
from infrastructure.utils.metrics_collector import MetricsCollector
from infrastructure.utils.worker_pool import WorkerPool
from presentation.controllers.cli import Cli
from infrastructure.factories.datacleaner_factory import datacleaner_factory


def cli_factory(config: ConfigPort, logger: LoggerPort) -> Cli:
    company_repository = CompanyDataRepository(config=config, logger=logger)

    datacleaner = datacleaner_factory(config, logger)
    mapper = CompanyDataMapper(datacleaner)
    metrics_collector = MetricsCollector()
    worker_pool = WorkerPool(config, metrics_collector, config.worker_pool.max_workers)
    http_client = RequestsAffinityHttpClient()
    company_scraper = CompanyDataScraper(
        config=config,
        logger=logger,
        datacleaner=datacleaner,
        mapper=mapper,
        metrics_collector=metrics_collector,
        worker_pool=worker_pool,
        http_client=http_client,
    )
    return Cli(
        config=config,
        logger=logger,
        company_repository=company_repository,
        company_scraper=company_scraper,
    )
