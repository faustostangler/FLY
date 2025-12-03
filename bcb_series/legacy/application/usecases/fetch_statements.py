"""Use cases for fetching raw statement rows."""

from __future__ import annotations

import time
from typing import Callable, List, Optional, Tuple

from domain.dto.nsd_dto import NsdDTO
from domain.dto.statement_raw_dto import StatementRawDTO
from domain.dto.worker_class_dto import WorkerTaskDTO
from domain.ports import (
    ConfigPort,
    LoggerPort,
    MetricsCollectorPort,
    RepositoryStatementFetchedPort,
    StatementRawRepositoryPort,
    WorkerPoolPort,
)
from domain.ports.scraper_ports import StatementsRawcraperPort
from infrastructure.helpers import ByteFormatter, SaveStrategy


class FetchStatementsUseCase:
    """Retrieve raw statement rows and persist them for later parsing."""

    def __init__(
        self,
        logger: LoggerPort,
        source: StatementsRawcraperPort,
        raw_statement_repository: StatementRawRepositoryPort,
        fetched_statements_repo: RepositoryStatementFetchedPort,
        metrics_collector: MetricsCollectorPort,
        worker_pool_executor: WorkerPoolPort,
        config: ConfigPort,
        max_workers: int = 1,
    ) -> None:
        """Store dependencies for fetching and saving raw rows."""
        self.logger = logger
        self.source = source
        self.fetched_statements_repo = fetched_statements_repo
        self.raw_statement_repository = raw_statement_repository
        self.config = config
        self.collector = metrics_collector
        self.worker_pool_executor = worker_pool_executor
        self.max_workers = max_workers

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def fetch_statement_rows(
        self,
        targets: list[NsdDTO] | None = None,
        batch_rows: list[NsdDTO] | None = None,
        save_callback: Optional[Callable[[List[StatementRawDTO]], None]] = None,
        threshold: Optional[int] = None,
    ) -> List[Tuple[NsdDTO, List[StatementRawDTO]]]:
        """Execute the use case for ``batch_rows``."""
        targets = targets or batch_rows
        # self.logger.log(
        #     "Run  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run(save_callback, threshold)",
        #     level="info",
        # )

        if not targets:
            return []

        # self.logger.log(
        #     "Call Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all(save_callback, threshold)",
        #     level="info",
        # )
        results = self.fetch_all(
            targets=targets,
            save_callback=save_callback,
            threshold=threshold,
        )
        # self.logger.log(
        #     "End  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all(save_callback, threshold)",
        #     level="info",
        # )

        # self.logger.log(
        #     "End  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run(save_callback, threshold)",
        #     level="info",
        # )

        return results

    def fetch_all(
        self,
        targets: List[NsdDTO],
        save_callback: Optional[Callable[[List[StatementRawDTO]], None]] = None,
        threshold: Optional[int] = None,
    ) -> List[Tuple[NsdDTO, List[StatementRawDTO]]]:
        """Fetch statements for ``targets`` concurrently."""
        # self.logger.log(
        #     "Run  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all(save_callback, threshold)",
        #     level="info",
        # )

        byte_formatter = ByteFormatter()
        # self.logger.log("End Instance worker_pool", level="info")

        # Initialize the saving strategy that buffers results.
        # self.logger.log("Instantiate strategy", level="info")
        strategy: SaveStrategy[StatementRawDTO] = SaveStrategy(
            save_callback or self.raw_statement_repository.save_all,
            threshold,
            config=self.config,
        )
        # self.logger.log("End Instance strategy", level="info")

        # Pair each target with its index for worker pool processing.
        tasks = list(enumerate(targets))

        collector = self.collector
        start_time = time.perf_counter()

        def processor(task: WorkerTaskDTO) -> Tuple[NsdDTO, List[StatementRawDTO]]:
            # self.logger.log(
            #     "Call Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all().processor().source.fetch()",
            #     level="info",
            # )
            attempt = 0

            bytes_before = collector.network_bytes
            fetched = self.source.fetch(task)
            lines = len(fetched["statements"])

            while lines == 0:
                attempt += 1
                quarter = (
                    fetched["nsd"].quarter.strftime("%Y-%m-%d")
                    if fetched["nsd"].quarter
                    else None
                )
                extra_info = {
                    "details": f"{fetched['nsd'].nsd} {fetched['nsd'].company_name} {quarter} {fetched['nsd'].version}",
                    "attempt": f"attempt {attempt}",
                }
                self.logger.warning(
                    f"Retrying {task.index + 1}/{len(tasks)}",
                    extra=extra_info,
                    worker_id=task.worker_id,
                )

                fetched = self.source.fetch(task)
                lines = len(fetched["statements"])

            download_bytes = collector.network_bytes - bytes_before

            quarter = (
                fetched["nsd"].quarter.strftime("%Y-%m-%d")
                if fetched["nsd"].quarter
                else None
            )
            extra_info = {
                "details": f"{fetched['nsd'].nsd} {fetched['nsd'].company_name} {quarter} {fetched['nsd'].version}",
                "lines": f"{len(fetched['statements'])} lines",
                "Download": byte_formatter.format_bytes(download_bytes),
                "Total download": byte_formatter.format_bytes(collector.network_bytes),
            }
            self.logger.info(
                f"Statement {task.index + 1}/{len(tasks)}",
                progress={
                    "index": task.index,
                    "size": len(tasks),
                    "start_time": start_time,
                },
                extra=extra_info,
                worker_id=task.worker_id,
            )

            # self.logger.log(
            #     "End  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all().processor().source.fetch()",
            #     level="info",
            # )

            return fetched["nsd"], fetched["statements"]

        def handle_batch(item: Tuple[NsdDTO, List[StatementRawDTO]]) -> None:
            """Buffer fetched statement rows via ``strategy``."""

            # ``SaveStrategy.handle`` can accept an iterable of rows, so pass
            # the entire list at once for more efficient buffering.
            strategy.handle(item[1])

        # self.logger.log(
        #     "Call Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all().worker_pool.run(tasks, processor, handle_batch)",
        #     level="info",
        # )
        result = self.worker_pool_executor.run(
            tasks=tasks,
            processor=processor,
            logger=self.logger,
            on_result=handle_batch,
        )
        # self.logger.log(
        #     "End  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all().worker_pool.run(tasks, processor, handle_batch)",
        #     level="info",
        # )

        strategy.finalize()

        # self.logger.log(
        #     "End  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all(save_callback, threshold)",
        #     level="info",
        # )

        return result.items
