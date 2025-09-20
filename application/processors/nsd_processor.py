from __future__ import annotations

import threading
import time
from datetime import date, datetime
from typing import Any, Iterable, Iterator, Mapping, Optional, Sequence, TypeVar, cast

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.polices.nsd_policy import NsdPolicyPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from domain.ports.scraper_base_port import SaveCallback
from domain.ports.scraper_nsd_port import ScraperNsdPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from domain.services.financial_normalizer import FinancialNormalizerPort
from domain.services.ratios_calculator import RatiosCalculatorPort
from infrastructure.utils.id_generator import IdGenerator
from infrastructure.utils.list_flatenner import ListFlattener

_T = TypeVar("_T")


def _chunked(items: Sequence[_T], chunk_size: int) -> Iterator[list[_T]]:
    """Yield ``items`` slices limited by ``chunk_size`` (defaults to 1 when invalid)."""

    size = max(1, int(chunk_size or 0))
    for start in range(0, len(items), size):
        yield list(items[start : start + size])


class _NsdTxnAggregator:
    """Mantém NSD, RAW e FETCHED juntos para flush atômico."""

    def __init__(
        self,
        *,
        save_callback: SaveCallback[NsdDTO],
        statements_raw_repository: RepositoryStatementsRawPort,
        statements_fetched_repository: RepositoryStatementFetchedPort,
        chunk_size: int,
    ) -> None:
        self._save_callback = save_callback
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository
        self._chunk_size = chunk_size if chunk_size > 0 else 1
        self._nsd_buffer: list[NsdDTO] = []
        self._raw_data: list[StatementRawDTO] = []
        self._fetched_data: list[StatementFetchedDTO] = []

    def set_nsd(self, nsd: NsdDTO) -> None:
        self._nsd_buffer.append(nsd)

    def add_raw_many(self, items: Iterable[StatementRawDTO]) -> None:
        self._raw_data.extend(items)

    def add_fetched_many(self, items: Iterable[StatementFetchedDTO]) -> None:
        self._fetched_data.extend(items)

    def flush(self, *, uow: Uow) -> None:
        if self._nsd_buffer:
            for chunk in _chunked(self._nsd_buffer, self._chunk_size):
                self._save_callback(chunk, uow=uow)
        if self._raw_data:
            for chunk in _chunked(self._raw_data, self._chunk_size):
                self.statements_raw_repository.save_all(chunk, uow=uow)
        if self._fetched_data:
            for chunk in _chunked(self._fetched_data, self._chunk_size):
                self.statements_fetched_repository.save_all(chunk, uow=uow)

        self._nsd_buffer.clear()
        self._raw_data.clear()
        self._fetched_data.clear()


class _StageTimeline:
    """Helper to measure time spent in each stage of the NSD pipeline."""

    def __init__(self, *, started_at: float | None = None) -> None:
        self._started_at = (
            started_at if started_at is not None else time.perf_counter()
        )
        self._last_mark = self._started_at
        self._durations: dict[str, float] = {}

    def mark(self, stage: str) -> str:
        """Record the elapsed time since the previous stage and return a summary."""

        now = time.perf_counter()
        self._durations[stage] = now - self._last_mark
        self._last_mark = now
        return self.summary()

    def summary(self) -> str:
        if not self._durations:
            return ""
        # parts = [
        #     f"{name.lower()}={self._format_duration(seconds)}"
        #     for name, seconds in self._durations.items()
        # ]
        return ""  # "pipeline: " + " ".join(parts)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"

        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        return f"{h}h{m:02}m{s:02}s"


class NsdProcessor:
    """Processa 1 NSD por vez. Cada tarefa abre sua própria UoW."""

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,
        nsd_repository: RepositoryNsdPort,
        company_repository: RepositoryCompanyDataPort,
        statements_raw_repository: RepositoryStatementsRawPort,
        statements_fetched_repository: RepositoryStatementFetchedPort,
        scraper_nsd: ScraperNsdPort,
        scraper_statements_raw: ScraperStatementRawPort,
        policy: NsdPolicyPort,
        financial_normalizer: FinancialNormalizerPort,
        ratios_calculator: RatiosCalculatorPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self.config = config
        self.logger = logger

        self.company_repository = company_repository
        self.nsd_repository = nsd_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository
        self.scraper_statements_raw = scraper_statements_raw

        self.scraper_nsd = scraper_nsd

        self.uow_factory = uow_factory
        self.policy = policy
        self.financial_normalizer = financial_normalizer
        self.ratios_calculator = ratios_calculator

        self.id_generator = IdGenerator(config=config)

        # Progress tracking helpers -------------------------------------------------
        self._progress_lock = threading.Lock()
        self._progress_started_at: float | None = None

    # compat com pools que chamam .run(task) ou chamam o objeto
    def __call__(self, task: WorkerTaskDTO) -> Any:
        return self.run(task)

    def run(self, task: WorkerTaskDTO) -> Any:
        nsd_id = task.data
        start_time = time.perf_counter()
        progress_start = self._resolve_progress_start_time(
            start_time, reset=task.index == 0
        )
        timeline = _StageTimeline(started_at=start_time)
        nsd = self.scraper_nsd.fetch_one(int(nsd_id))
        progress = self._build_progress_payload(task=task, start_time=progress_start)

        if nsd is None:
            summary = timeline.mark("NSD")
            missing_progress = dict(progress)
            missing_progress["stage"] = "NSD"
            self._log_message(
                f"NSD {nsd_id}",
                progress=missing_progress,
                worker_id=task.worker_id,
                extra_info=[summary] if summary else None,
            )
            return task.data

        with self.uow_factory() as uow:
            self._ensure_company_exists(nsd.company_name, uow=uow)
            nsd_type = self.policy.identify_type(nsd)

            aggregator = self._create_aggregator()
            self._log_stage(
                "NSD",
                nsd,
                progress=progress,
                worker_id=task.worker_id,
                timeline=timeline,
            )

            if not nsd_type.is_statement:
                self._finalize_nsd(nsd=nsd, aggregator=aggregator, uow=uow)
                return nsd

            return self._process_statement_nsd(
                nsd=nsd,
                task=task,
                progress=progress,
                aggregator=aggregator,
                uow=uow,
                timeline=timeline,
            )

    def _process_statement_nsd(
        self,
        *,
        nsd: NsdDTO,
        task: WorkerTaskDTO,
        progress: dict[str, Any],
        aggregator: _NsdTxnAggregator,
        uow: Uow,
        timeline: _StageTimeline,
    ) -> Any:
        quarter_police = self.policy.normalize_quarter(nsd)
        sent_date = getattr(nsd, "sent_date")
        if hasattr(sent_date, "date"):
            sent_date = sent_date.date()
        when = sent_date or date(quarter_police.year, quarter_police.month, 1)
        recency = self.policy.compute_recency_window(when)
        action = self.policy.decide_action(
            year=quarter_police.year,
            quarter=quarter_police.month,
            version=nsd.version,
            is_december=quarter_police.is_december,
            is_recent=recency.is_recent,
        )

        raw_lines = self._fetch_raw_lines(nsd=nsd, task=task)
        self._log_stage(
            "RAW",
            nsd,
            progress=progress,
            worker_id=task.worker_id,
            timeline=timeline,
        )

        if action.is_raw():
            aggregator.add_raw_many(raw_lines)
            self._finalize_nsd(nsd=nsd, aggregator=aggregator, uow=uow)
            return nsd

        try:
            year_view = list(
                self.statements_raw_repository.get_company_year_view(
                    company_name=nsd.company_name,
                    year=quarter_police.year,
                    uow=uow,
                )
            )
            combined: list[StatementRawDTO] = [*year_view, *raw_lines]
            deduped = self.policy.version_deduplicate(combined)
            quarterized = self.financial_normalizer.quarterize(deduped)
            standardized_rows = list(self.financial_normalizer.standardize(quarterized))
            ratios = list(
                self.ratios_calculator.calculate(
                    cast(Sequence[StatementFetchedDTO], standardized_rows)
                )
            )
            fetched_rows: list[StatementFetchedDTO] = [*standardized_rows, *ratios]

            self._log_stage(
                "FTD",
                nsd,
                progress=progress,
                worker_id=task.worker_id,
                timeline=timeline,
            )

            aggregator.add_raw_many(raw_lines)
            aggregator.add_fetched_many(self._filter_new_fetched(fetched_rows, uow=uow))
            self._finalize_nsd(nsd=nsd, aggregator=aggregator, uow=uow)

            return nsd
        except Exception as exc:
            self.logger.log(str(exc))
            return None

    def _fetch_raw_lines(self, *, nsd: NsdDTO, task: WorkerTaskDTO) -> list[StatementRawDTO]:
        raw_task = WorkerTaskDTO(
            index=task.index,
            data=nsd,
            worker_id=task.worker_id,
            total_size=task.total_size,
        )
        raw_result: Mapping[str, Sequence[StatementRawDTO]] = self.scraper_statements_raw.fetch(
            raw_task
        )
        return list(raw_result["items"])

    def _finalize_nsd(
        self,
        *,
        nsd: NsdDTO,
        aggregator: _NsdTxnAggregator,
        uow: Uow,
    ) -> None:
        aggregator.set_nsd(nsd)
        aggregator.flush(uow=uow)
        uow.commit()

    def _create_aggregator(self) -> _NsdTxnAggregator:
        return _NsdTxnAggregator(
            save_callback=self._save_batch,
            statements_raw_repository=self.statements_raw_repository,
            statements_fetched_repository=self.statements_fetched_repository,
            chunk_size=self._resolve_persistence_threshold(),
        )

    def _resolve_persistence_threshold(self) -> int:
        raw_threshold = getattr(self.config.repository, "persistence_threshold", None)
        try:
            threshold = int(raw_threshold) if raw_threshold is not None else 0
        except (TypeError, ValueError):
            threshold = 0

        if threshold <= 0:
            return 50
        return threshold

    def _resolve_progress_start_time(
        self, candidate: float, *, reset: bool = False
    ) -> float:
        """Return a shared start time for progress calculations.

        The first task processed defines the baseline `start_time`. Subsequent
        tasks reuse this timestamp so that elapsed time reflects the entire
        batch execution instead of the duration of a single NSD pipeline.

        Args:
            candidate: Monotonic timestamp captured for the current task.
            reset: When True, force the shared start time to this candidate.
        """

        with self._progress_lock:
            if reset or self._progress_started_at is None:
                self._progress_started_at = candidate
            return self._progress_started_at

    def _build_progress_payload(self, *, task: WorkerTaskDTO, start_time: float) -> dict[str, Any]:
        raw_total = task.total_size or (task.index + 1)
        try:
            total_size = int(raw_total)
        except (TypeError, ValueError):  # pragma: no cover - defensive fallback
            total_size = task.index + 1

        if total_size <= 0:
            total_size = 1

        return {
            "index": task.index,
            "size": total_size,
            "start_time": start_time,
        }

    def _log_stage(
        self,
        stage: str,
        nsd: NsdDTO,
        *,
        progress: dict[str, Any],
        worker_id: str,
        timeline: _StageTimeline | None = None,
    ) -> None:
        extra_tokens = [self._format_extra_info_line(nsd)]
        if timeline is not None:
            summary = timeline.mark(stage)
            if summary:
                extra_tokens.append(summary)
        stage_progress = dict(progress)
        stage_progress["stage"] = stage

        self._log_message(
            f"{stage} {nsd.nsd}",
            progress=stage_progress,
            worker_id=worker_id,
            extra_info=extra_tokens,
        )

    def _log_message(
        self,
        message: str,
        *,
        progress: dict[str, Any],
        worker_id: str,
        extra_info: Sequence[str] | None = None,
    ) -> None:
        payload = dict(progress)
        if extra_info is not None:
            payload["extra_info"] = list(extra_info)
        self.logger.log(message, level="info", progress=payload, worker_id=worker_id)

    def _format_extra_info_line(self, nsd: NsdDTO) -> str:
        quarter = (
            nsd.quarter.strftime("%Y-%m-%d")
            if isinstance(nsd.quarter, datetime)
            else nsd.quarter
        )
        quarter_display = quarter or ""
        sent_date = nsd.sent_date or ""
        return (
            f"{quarter_display} v{nsd.version} | "
            f"{sent_date} | "
            f"{nsd.nsd_type} {nsd.company_name}"
        )

    def _filter_new_fetched(
        self,
        rows: Sequence[StatementFetchedDTO],
        *,
        uow: Uow,
    ) -> list[StatementFetchedDTO]:
        """Remove duplicates within the current batch using natural keys."""

        _ = uow  # retained for signature compatibility

        if not rows:
            return []

        unique_rows: list[StatementFetchedDTO] = []
        seen_keys: set[tuple[Any, ...]] = set()

        for row in rows:
            key = (
                row.nsd,
                row.company_name,
                row.quarter,
                row.version,
                row.grupo,
                row.quadro,
                row.account,
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique_rows.append(row)

        return unique_rows

    def _ensure_company_exists(
        self, company_name: Optional[str], *, uow: Uow
    ) -> Optional[str]:
        if not company_name:
            return None

        cvm = self.company_repository.get_cvm_by_name(company_name, uow=uow)
        if cvm:
            return cvm

        dto = CompanyDataDTO(
            cvm_code=self.id_generator.create_id(size=6),
            company_name=company_name,
        )
        self.company_repository.save_all([dto], uow=uow)
        return dto.cvm_code

    def _save_batch(
        self,
        items: list[NsdDTO],
        *,
        uow: Uow,
    ) -> None:
        """Persist a batch of NSD DTOs within the provided unit of work."""

        flat_items = cast(list[NsdDTO | None], ListFlattener.flatten(items))
        if not flat_items:
            return

        dtos: list[NsdDTO] = []
        for item in flat_items:
            if item is None:
                continue
            if isinstance(item, NsdDTO):
                dtos.append(NsdDTO.from_raw(item))
            else:  # pragma: no cover - defensive path for compatible objects
                dtos.append(NsdDTO.from_raw(cast(NsdDTO, item)))

        if not dtos:
            return

        company_names = {dto.company_name for dto in dtos if dto.company_name}
        threshold = self._resolve_persistence_threshold()

        if company_names:
            existing = {
                name
                for (name,) in self.company_repository.iter_existing_by_columns(
                    "company_name", uow=uow
                )
            }
            missing = company_names - existing
            if missing:
                to_create = [
                    CompanyDataDTO(
                        cvm_code=self.id_generator.create_id(size=6),
                        company_name=name,
                    )
                    for name in missing
                ]
                for chunk in _chunked(to_create, threshold):
                    self.company_repository.save_all(chunk, uow=uow)

        for chunk in _chunked(dtos, threshold):
            self.nsd_repository.save_all(chunk, uow=uow)
