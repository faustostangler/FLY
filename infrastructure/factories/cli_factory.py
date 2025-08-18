from domain.ports import ConfigPort, LoggerPort
from infrastructure.factories import datacleaner_factory
from infrastructure.utils import MetricsCollector, WorkerPool
from presentation.controllers import Cli


def cli_factory(config: ConfigPort, logger: LoggerPort) -> Cli:
    datacleaner = datacleaner_factory(config, logger)
    metrics_collector = MetricsCollector()
    worker_pool = (config, metrics_collector, max_workers=None)
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

    )
