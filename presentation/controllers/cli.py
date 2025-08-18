from application.mappers import CompanyDataMapper
from domain.ports import (
    CompanyDataRepositoryPort,
    ConfigPort,
    DataCleanerPort,
    LoggerPort,
    MetricsCollectorPort,
    WorkerPoolPort,
)


class Cli():
    def __init__(self, config: ConfigPort, logger: LoggerPort, datacleaner: DataCleanerPort,
                 metrics_collector: MetricsCollectorPort, worker_pool: WorkerPoolPort,
                 company_repository: CompanyDataRepositoryPort
                 ) -> None:
        self.config = config
        self.logger = logger
        self.datacleaner = datacleaner
        self.metrics_collector = metrics_collector
        self.company_repository = company_repository

    def run(self) -> None:
        self.logger.log("Start FLY", level="info")
        # Aqui você chama os processors, controllers, etc.
        self._company_service()

    def _company_service(self) -> None:
        """Build and execute the company data synchronization flow."""
        mapper = CompanyDataMapper(self.datacleaner)

        company_repository = self.company_repository

        company_scraper = CompanyDataScraper(
            config=self.config,
            logger=self.logger,
            data_cleaner=self.data_cleaner,
            mapper=mapper,
            worker_pool_executor=self.worker_pool_executor,
            metrics_collector=self.collector,
            http_client=self.http_client,
        )
        company_service = CompanyDataService(
            config=self.config,
            logger=self.logger,
            repository=company_repository,
            scraper=company_scraper,
        )
        company_service.sync_companies()

