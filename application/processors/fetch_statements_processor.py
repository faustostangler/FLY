"""Processor for fetching financial statement rows."""

from __future__ import annotations

from typing import Callable, DefaultDict, Dict, List, Optional, Tuple, TypeAlias
from collections import defaultdict

from application.usecases.fetch_statements import FetchStatementsUseCase
from domain.dto import NsdDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import (
    CompanyDataRepositoryPort,
    ConfigPort,
    LoggerPort,
    MetricsCollectorPort,
    NSDRepositoryPort,
    ParsedStatementRepositoryPort,
    RawStatementRepositoryPort,
    WorkerPoolPort,
)
from domain.ports.scraper_ports import RawStatementScraperPort

from .base_processor import BaseProcessor


LoadPayload: TypeAlias = Tuple[
    List[NsdDTO],
    Optional[Callable[[List[RawStatementDTO]], None]],
    Optional[int],
]
RowsByNsd: TypeAlias = List[Tuple[NsdDTO, List[RawStatementDTO]]]
PersistedPayload: TypeAlias = RowsByNsd


class FetchStatementsProcessor(BaseProcessor[LoadPayload, RowsByNsd, PersistedPayload]):
    """Fetch raw statements for pending NSDs."""

    def __init__(
        self,
        logger: LoggerPort,
        config: ConfigPort,
        source: RawStatementScraperPort,
        company_repo: CompanyDataRepositoryPort,
        nsd_repo: NSDRepositoryPort,
        raw_statement_repo: RawStatementRepositoryPort,
        parsed_statements_repo: ParsedStatementRepositoryPort,
        metrics_collector: MetricsCollectorPort,
        worker_pool_executor: WorkerPoolPort,
        max_workers: int = 1,
    ) -> None:
        """Store dependencies for the processor."""
        self.logger = logger
        self.config = config
        self.source = source
        self.company_repo = company_repo
        self.nsd_repo = nsd_repo
        self.raw_statement_repo = raw_statement_repo
        self.parsed_statements_repo = parsed_statements_repo
        self.collector = metrics_collector
        self.worker_pool_executor = worker_pool_executor
        self.max_workers = max_workers

        self.fetch_usecase = FetchStatementsUseCase(
            logger=self.logger,
            config=self.config,
            source=source,
            raw_statement_repository=raw_statement_repo,
            parsed_statements_repo=parsed_statements_repo,
            metrics_collector=self.collector,
            worker_pool_executor=self.worker_pool_executor,
            max_workers=self.max_workers,
        )

    def _build_targets(self) -> List[NsdDTO]:
        """Return NSD identifiers that still need fetching."""
        company_names = {
            c.company_name for c in self.company_repo.iter_all() if c.company_name
        }
        if not company_names:
            return []

        raw_statement_rows_with_nsd_processed = {
            int(row[0])
            for row in self.raw_statement_repo.iter_existing_by_columns("nsd")
        }
        valid_types = set(self.config.domain.statements_types)

        results: List[NsdDTO] = []
        for nsd in self.nsd_repo.iter_all():
            if (
                nsd.company_name
                and nsd.company_name in company_names
                and nsd.nsd_type in valid_types
                and nsd.nsd not in raw_statement_rows_with_nsd_processed
            ):
                results.append(nsd)
        results.sort(key=lambda nsd: (nsd.company_name, nsd.quarter, nsd.version))

        return results

    def run(
        self,
        save_callback: Optional[Callable[[List[RawStatementDTO]], None]] = None,
        threshold: Optional[int] = None,
    ) -> RowsByNsd:
        """Run the fetch pipeline."""
        data: LoadPayload = self.load(save_callback=save_callback, threshold=threshold)
        transformed: RowsByNsd = self.transform(data)
        transformed: RowsByNsd = self._load_transformed()
        result: PersistedPayload = self.persist(transformed)
        return result

    def load(
        self,
        save_callback = None,
        threshold = None,
    ) -> Tuple[
        List[NsdDTO], Optional[Callable[[List[RawStatementDTO]], None]], Optional[int]
    ]:
        """Prepare targets and forward optional persistence parameters."""
        targets = self._build_targets()
        return targets, save_callback, threshold

    def transform(
        self,
        data: Tuple[
            List[NsdDTO],
            Optional[Callable[[List[RawStatementDTO]], None]],
            Optional[int],
        ],
    ) -> PersistedPayload:
        """Fetch statement rows for ``targets`` using the use case."""
        targets, save_callback, threshold = data
        if not targets:
            return []
        return self.fetch_usecase.fetch_statement_rows(
            batch_rows=targets, save_callback=save_callback, threshold=threshold
        )

    def persist(
        self, data: PersistedPayload
    ) -> PersistedPayload:
        """No-op persist step; the use case already saves rows."""
        return data

    def _load_transformed(self) -> List[Tuple[NsdDTO, List[RawStatementDTO]]]:
        """Lê o DB e monta [(NsdDTO, [RawStatementDTO, ...])] apenas para o primeiro nsd encontrado."""
        company_names = [company.company_name for company in self.company_repo.iter_all()]
        company_name = '2W ECOBANK SA'

        raw_statements = self.raw_statement_repo.get_by_company_name(company_name=company_name)

        # 2) agrupa por nsd (normalizando para int) e reforça o filtro por companhia
        buckets: Dict[int, List[RawStatementDTO]] = defaultdict(list)
        for row in raw_statements:
            if getattr(row, "company_name", None) != company_name:
                continue
            try:
                nsd_id = int(getattr(row, "nsd"))
            except (TypeError, ValueError):
                continue
            buckets[nsd_id].append(row)
        if not buckets:
            return []

        # 3) indexa NsdDTO por nsd, apenas desta companhia
        nsd_index: Dict[int, NsdDTO] = {}
        for nsd in self.nsd_repo.iter_all():
            if nsd.company_name == company_name:
                nsd_index[nsd.nsd] = nsd

        # 4) monta os pares apenas quando existir NsdDTO correspondente
        pairs: List[Tuple[NsdDTO, List[RawStatementDTO]]] = [
            (nsd_index[nsd_id], rows)
            for nsd_id, rows in buckets.items()
            if nsd_id in nsd_index
        ]

        # 5) ordena como no _build_targets para previsibilidade
        pairs.sort(key=lambda p: (p[0].company_name or "", p[0].quarter, p[0].version))

        return pairs
