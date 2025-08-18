from domain.ports import ConfigPort, DataCleanerPort, LoggerPort, MetricsCollectorPort


class Cli():
    def __init__(self, config: ConfigPort, logger: LoggerPort, datacleaner: DataCleanerPort, metrics_collector: MetricsCollectorPort) -> None:
        self.config = config
        self.logger = logger
        self.datacleaner = datacleaner
        self.metrics_collector =  metrics_collector

    def run(self) -> None:
        self.logger.log("Start FLY", level="info")
        # Aqui você chama os processors, controllers, etc.
        self._company_service()

    def _company_service(self) -> None:
        """Build and execute the company data synchronization flow."""
        mapper = CompanyDataMapper(self.data_cleaner)
        company_repo = self.company_repo
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
            repository=company_repo,
            scraper=company_scraper,
        )
        company_service.sync_companies()

