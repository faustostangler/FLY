# infrastructure/adapters/scraper_stock_quote.py
from __future__ import annotations
import calendar
from datetime import datetime, date, timedelta
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

IndicatorsExistingItem = Tuple[str, str, str, datetime | None, datetime]


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

        endpoint_template = self.config.indicators.endpoint["bcb"]
        default_start_date = datetime.strptime("01/01/1900", "%d/%m/%Y")

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

            code_series, name, periodicity, start_date, end_date = entry

            start_dt = (
                start_date
                if isinstance(start_date, datetime)
                else datetime.combine(start_date, datetime.min.time())
                if isinstance(start_date, date)
                else default_start_date
            )
            end_dt = (
                end_date
                if isinstance(end_date, datetime)
                else datetime.combine(end_date, datetime.min.time())
                if isinstance(end_date, date)
                else datetime.today()
            )

            try:
                parsed_records: List[IndicatorRecordDTO] = []

                today = datetime.today()
                last_request_end: datetime | None = None

                # Prepare diagnostic metadata for logs
                extra_info = {
                    "code_series": code_series,
                    "name": name[:32],
                    # "periodicity": periodicity,
                    # "period": f' {end_dt.strftime("%d/%m/%Y")}', 
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

                # chunk url processing
                for chunk_start, chunk_end in self._chunk_date_ranges(start_dt, end_dt):
                    resolved_window = self._resolve_request_window(
                        chunk_start,
                        chunk_end,
                        periodicity,
                        today=today,
                    )
                    if resolved_window is None:
                        continue

                    request_start, request_end = resolved_window

                    chunk_url = endpoint_template.format(
                        codigo_serie=code_series,
                        dataInicial=request_start.strftime("%d/%m/%Y"),
                        dataFinal=request_end.strftime("%d/%m/%Y"),
                    )

                    try:
                        with self.http_client.borrow_session() as session:
                            body = self.http_client.fetch_with(
                                session, chunk_url, headers=session.headers
                            )

                        parsed_chunk = self._parse_json(
                            body.decode("utf-8"),
                            name=name,
                            code_series=code_series,
                        )
                        parsed_records.extend(parsed_chunk)

                    finally:
                        continue

                return parsed_records

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


    def _chunk_date_ranges(
        self, start: datetime, end: datetime, years: int = 10
    ) -> Iterable[Tuple[datetime, datetime]]:
        if start > end:
            return

        chunk_start = start
        while chunk_start <= end:
            tentative_end = self._safe_add_years(chunk_start, years)
            chunk_end = tentative_end if tentative_end <= end else end

            yield chunk_start, chunk_end

            if chunk_end >= end:
                break

            chunk_start = chunk_end + timedelta(days=1)

    def _resolve_request_window(
        self,
        chunk_start: datetime,
        chunk_end: datetime,
        periodicity: str,
        *,
        today: datetime,
    ) -> Optional[Tuple[datetime, datetime]]:
        normalized = (periodicity or "").strip().lower()

        if normalized == "monthly":
            adjusted_end = chunk_end
            while adjusted_end >= chunk_start:
                candidate_end = self._first_day_of_next_month(adjusted_end)
                if candidate_end <= today:
                    return chunk_start, candidate_end
                adjusted_end -= timedelta(days=1)
            return None

        effective_end = min(chunk_end, today)
        if effective_end < chunk_start:
            return None

        return chunk_start, effective_end

    def _safe_add_years(self, dt: datetime, years: int) -> datetime:
        target_year = dt.year + years
        try:
            return dt.replace(year=target_year)
        except ValueError:
            # Handles leap day for non-leap target years
            return dt.replace(year=target_year, day=28)

    def _first_day_of_next_month(self, dt: datetime) -> datetime:
        return self._add_months(dt.replace(day=1), 1)

    def _add_months(self, dt: datetime, months: int) -> datetime:
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1
        day = min(dt.day, calendar.monthrange(year, month)[1])
        return dt.replace(year=year, month=month, day=day)


