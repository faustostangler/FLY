from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any, Iterable, Mapping, Optional, Sequence, cast

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
from domain.ports.scraper_nsd_port import ScraperNsdPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from domain.services.financial_normalizer import FinancialNormalizerPort
from domain.services.ratios_calculator import RatiosCalculatorPort
from infrastructure.utils.id_generator import IdGenerator


class _NsdTxnAggregator:
    """Mantém NSD, RAW e FETCHED juntos para flush atômico."""

    def __init__(
        self,
        *,
        nsd_repository: RepositoryNsdPort,
        statements_raw_repository: RepositoryStatementsRawPort,
        statements_fetched_repository: RepositoryStatementFetchedPort,
    ) -> None:
        self.nsd_repository = nsd_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository
        self._nsd_data: NsdDTO | None = None
        self._raw_data: list[StatementRawDTO] = []
        self._fetched_data: list[StatementFetchedDTO] = []

    def set_nsd(self, nsd: NsdDTO) -> None:
        self._nsd_data = nsd

    def add_raw_many(self, items: Iterable[StatementRawDTO]) -> None:
        self._raw_data.extend(items)

    def add_fetched_many(self, items: Iterable[StatementFetchedDTO]) -> None:
        self._fetched_data.extend(items)

    def flush(self, *, uow: Uow) -> None:
        if self._nsd_data is not None:
            self.nsd_repository.save_all([self._nsd_data], uow=uow)
        if self._raw_data:
            self.statements_raw_repository.save_all(self._raw_data, uow=uow)
        if self._fetched_data:
            self.statements_fetched_repository.save_all(self._fetched_data, uow=uow)

        self._nsd_data = None
        self._raw_data.clear()
        self._fetched_data.clear()


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

    # compat com pools que chamam .run(task) ou chamam o objeto
    def __call__(self, task: WorkerTaskDTO) -> Any:
        return self.run(task)

    def run(self, task: WorkerTaskDTO) -> Any:
        nsd_id = task.data
        start_time = time.perf_counter()
        nsd = self.scraper_nsd.fetch_one(int(nsd_id))
        progress = self._build_progress_payload(task=task, start_time=start_time)

        if nsd is None:
            self._log_message(
                f"NSD {nsd_id}",
                progress=progress,
                worker_id=task.worker_id,
                extra_info=[""],
            )
            return task.data

        with self.uow_factory() as uow:
            self._ensure_company_exists(nsd.company_name, uow=uow)
            nsd_type = self.policy.identify_type(nsd)

            aggregator = self._create_aggregator()
            self._log_stage("NSD", nsd, progress=progress, worker_id=task.worker_id)

            if not nsd_type.is_statement:
                self._finalize_nsd(nsd=nsd, aggregator=aggregator, uow=uow)
                return nsd

            return self._process_statement_nsd(
                nsd=nsd,
                task=task,
                progress=progress,
                aggregator=aggregator,
                uow=uow,
            )

    def _process_statement_nsd(
        self,
        *,
        nsd: NsdDTO,
        task: WorkerTaskDTO,
        progress: dict[str, Any],
        aggregator: _NsdTxnAggregator,
        uow: Uow,
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
        self._log_stage("RAW", nsd, progress=progress, worker_id=task.worker_id)

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

            self._log_stage("FTD", nsd, progress=progress, worker_id=task.worker_id)

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
            nsd_repository=self.nsd_repository,
            statements_raw_repository=self.statements_raw_repository,
            statements_fetched_repository=self.statements_fetched_repository,
        )

    def _build_progress_payload(self, *, task: WorkerTaskDTO, start_time: float) -> dict[str, Any]:
        return {
            "index": task.index,
            "size": task.total_size,
            "start_time": start_time,
        }

    def _log_stage(
        self,
        stage: str,
        nsd: NsdDTO,
        *,
        progress: dict[str, Any],
        worker_id: str,
    ) -> None:
        self._log_message(
            f"{stage} {nsd.nsd}",
            progress=progress,
            worker_id=worker_id,
            extra_info=[self._format_extra_info_line(nsd)],
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
        return (
            f"{nsd.nsd} {quarter_display} | {nsd.sent_date} "
            f"v{nsd.version} | {nsd.nsd_type} {nsd.company_name}"
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
