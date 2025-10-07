# infrastructure/adapters/scraper_stock_quote.py
from __future__ import annotations
import calendar
from datetime import datetime, date
import time
import pandas as pd
from typing import Iterable, Optional, List, Tuple, cast
import json
import yfinance as yf  # dependência de infraestrutura

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.metrics_collector_port import MetricsCollectorPort
from application.ports.uow_port import Uow, UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.ports.http_client_port import AffinityHttpClientPort
from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.scraper_base_port import ExistingItem, SaveCallback
from domain.ports.scraper_indicators_port import ScraperIndicatorsPort

from infrastructure.utils.byte_formatter import ByteFormatter
from infrastructure.utils.save_strategy import SaveStrategy

IndicatorsExistingItem = Tuple[str, str, datetime | None, datetime]


class IndicatorsScraper(ScraperIndicatorsPort):
    """Scraper de cotações com delta por ticker e saída em DTO."""

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,
        repository_indicators: RepositoryIndicatorsPort,
        metrics_collector: MetricsCollectorPort,
        worker_pool: WorkerPoolPort,
        http_client: AffinityHttpClientPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self.config = config
        self.logger = logger
        self.repository_indicators = repository_indicators

        self.worker_pool_executor = worker_pool
        self._metrics_collector = metrics_collector
        self.uow_factory = uow_factory
        self.http_client = http_client

        self.byte_formatter = ByteFormatter()

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        existing_codes: Optional[Iterable[ExistingItem]] = None,
        save_callback: Optional[SaveCallback[IndicatorRecordDTO]] = None,
        **kwargs,
    ) -> List[IndicatorRecordDTO]:
        """Stream de DTOs de `start..end` e persistência opcional em lotes."""

        # Normalize list of codes to a deterministic sequence for processing
        self.existing_codes = list(existing_codes or [])

        # Determine persistence threshold (explicit > config > default)
        self.threshold = threshold or self.config.repository.persistence_threshold or 50

        # adapter para a estratégia
        def _adapter(items: List[IndicatorRecordDTO], *, uow: Uow) -> None:
            if save_callback is not None:
                save_callback(items, uow=uow)

        # Build a save strategy that buffers detail DTOs and flushes on threshold
        strategy: SaveStrategy[IndicatorRecordDTO] = SaveStrategy.from_config(
            _adapter if save_callback else None,
            self.threshold,
            config=self.config,
            uow_factory=self.uow_factory,
        )

        # Pair each entry with its index for progress reporting
        tasks = list(enumerate(self.existing_codes))

        # Mark the start time for progress ETA computations
        start_time = time.perf_counter()


        # Worker that processes a single company entry through the detail pipeline
        def processor(task: WorkerTaskDTO) -> List[IndicatorRecordDTO]:
            index = task.index
            entry = cast(IndicatorsExistingItem, task.data)
            worker_id = task.worker_id

            name, code_series, start_date, end_date = entry

            start = start_date or datetime(1900, 1, 1)
            start_str = start.strftime("%d/%m/%Y")
            end_str = end_date.strftime("%d/%m/%Y")
            url = self.config.indicators.endpoint["bcb"].format(
                codigo_serie=code_series,
                dataInicial=start_str,
                dataFinal=end_str,
            )

            try:
                with self.http_client.borrow_session() as session:
                    body = self.http_client.fetch_with(session, url, headers=session.headers)

                parsed = self._parse_json(
                    body.decode("utf-8"),
                    name=name,
                    code_series=code_series,
                )

                # Prepare diagnostic metadata for logs
                extra_info = {
                    "code_series": code_series, 
                    "name": name,
                    "download": self.byte_formatter.format_bytes(self._metrics_collector.download_bytes),
                    "total_download": self.byte_formatter.format_bytes(self._metrics_collector.network_bytes),
                }
                # Emit structured progress log for this item
                self.logger.log(
                    f"{code_series}",
                    level="info",
                    progress={
                        "index": index,
                        "size": len(tasks),
                        "start_time": start_time,
                    },
                    extra=extra_info,
                    worker_id=worker_id,
                )

                return parsed

            except Exception as e:
                self.logger.log(f"Failed to fetch: {code_series} {e}", level="warning")
                return []


        # Handler that buffers items and triggers flushes via the strategy
        def handle_batch(batch: List[IndicatorRecordDTO]) -> None:
            try:
                strategy.handle(batch)
            except Exception as e:
                for item in batch:
                    strategy.handle(item)

        try:
            # Execute detail processing concurrently
            pool_results = self.worker_pool_executor.run(
                tasks=tasks,
                processor=processor,
                logger=self.logger,
                on_result=handle_batch,
                max_workers=self.config.worker_pool.max_workers or 1,
                total_size=len(tasks),
            )

            # Ensure any residual buffered items are flushed
            strategy.finalize()
        except Exception as e:
            pass

        # Flatten nested worker results, skipping empty batches
        results: List[IndicatorRecordDTO] = [
            dto
            for batch in pool_results
            if batch
            for dto in batch
        ]

        # Return aggregated results and preserve execution metrics
        return results

    def _parse_json(
        self,
        raw: str,
        *,
        name: str,
        code_series: str,
    ) -> List[IndicatorRecordDTO]:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}") from e

        if not isinstance(payload, Iterable):
            raise ValueError("Payload não é uma coleção")

        out: List[IndicatorRecordDTO] = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            ds = row.get("data")
            vs = row.get( "valor")
            if ds is None or vs is None:
                continue

            # datas "01/08/2025"
            dt = datetime.strptime(str(ds).strip(), "%d/%m/%Y")

            # números "1.31" ou "1,31"
            num_str = str(vs).strip()
            if num_str in {"", "NaN", "nan", "None"}:
                continue
            try:
                value = float(num_str)
            except ValueError:
                continue

            out.append(IndicatorRecordDTO(
                source="BCB",
                name=str(name),
                code=str(code_series),
                date=dt,
                value=value,
            ))
        return out

    def get_metrics(self) -> int:
        return self._metrics_collector.network_bytes



    # def _save_date(self, val):
    #     if isinstance(val, pd.Series):
    #         val = val
    #     if isinstance(val, pd.Timestamp):
    #         return val.date()
    #     if isinstance(val, datetime):
    #         return val.date()
    #     if isinstance(val, date):
    #         return val
    #     return pd.to_datetime(val).date()


    # def _safe_float(self, val: object, default: float = 0.0) -> float:
    #     return default if pd.isna(val) else float(val)

    # def _safe_int(self, val: object, default: int = 0) -> int:
    #     return default if pd.isna(val) else int(val)


