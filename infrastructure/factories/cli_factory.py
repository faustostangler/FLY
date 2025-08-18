from domain.ports import ConfigPort, LoggerPort
from presentation.controllers import Cli
from infrastructure.factories import datacleaner_factory

def cli_factory(config: ConfigPort, logger: LoggerPort) -> Cli:
    datacleaner = datacleaner_factory(config, logger)
    collector = MetricsCollector()
    worker_pool = WorkerPool(config, metrics_collector=collector, ...)
    ...
    return Cli(
        config=config,
        logger=logger,
        data_cleaner=data_cleaner,
        metrics_collector=collector,
        company_repo=company_repo,
        ...
    )
