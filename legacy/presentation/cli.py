"""Command line interface that wires together the application services."""

from application import CompanyDataMapper
from application.processors.fetch_statements_processor import FetchStatementsProcessor
from application.processors.parse_statements_processor import ParseStatementsProcessor
from application.processors.transform_statements_processor import (
    TransformStatementsProcessor,
)
from application.services.company_data_service import CompanyDataService
from application.services.nsd_service import NsdService
from domain.ports import ConfigPort, LoggerPort
from infrastructure.helpers import WorkerPool
from infrastructure.helpers.metrics_collector import MetricsCollector
from infrastructure.http.circuit_breaker import BreakerPolicy, CircuitBreakerScraper
from infrastructure.http.rate_limiter import RateLimitedScraper, TokenBucket
from infrastructure.http.session_pool import SessionPool
from infrastructure.repositories import (
    SqlAlchemyCompanyDataRepository,
    SqlAlchemyNsdRepository,
    SqlAlchemyParsedStatementRepository,
    SqlAlchemyRawStatementRepository,
)
from infrastructure.repositories.http_cache_repository import HttpCacheRepository
from infrastructure.scrapers import (
    CompanyDataScraper,
    NsdScraper,
    RawStatementScraper,  # scraper de alto nível (port da aplicação)
    RequestsRawStatementScraper,  # cliente HTTP de baixo nível
)


class CLIAdapter:
    """Orchestrate FLY application flows via the command line."""

    def __init__(self, config: ConfigPort, logger: LoggerPort, data_cleaner) -> None:
        self.config = config
        self.logger = logger
        self.data_cleaner = data_cleaner

        self.collector = MetricsCollector()
        self.worker_pool_executor = WorkerPool(
            self.config,
            metrics_collector=self.collector,
            max_workers=self.config.global_settings.max_workers or 1,
        )
        self.company_repo = SqlAlchemyCompanyDataRepository(
            database_url=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        self.session_pool = SessionPool(
            self.config, self.logger, size=self.config.http.session_pool_size
        )
        self.http_cache = HttpCacheRepository(self.company_repo.session_factory)
        base_scraper = RequestsRawStatementScraper(
            config=self.config,
            logger=self.logger,
            metrics=self.collector,
            pool=self.session_pool,
            cache=self.http_cache,
            timeout=(
                self.config.http.timeout_connect,
                self.config.http.timeout_read,
            ),
        )
        bucket = TokenBucket(
            rate_per_sec=self.config.http.rate_per_sec,
            burst=self.config.http.burst,
        )
        limited = RateLimitedScraper(base_scraper, bucket, self.logger)
        self.http_client = CircuitBreakerScraper(
            limited,
            self.logger,
            policy=BreakerPolicy(
                failure_threshold=self.config.http.circuit_failures,
                open_seconds=self.config.http.circuit_open_seconds,
            ),
        )

    def start_fly(self) -> None:
        """Trigger all main processing pipelines for the FLY system."""
        self._company_service()
        self._nsd_service()
        self._statement_service()

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

    def _nsd_service(self) -> None:
        """Build and execute the NSD data synchronization flow."""
        company_repo = self.company_repo
        nsd_repo = SqlAlchemyNsdRepository(
            database_url=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        nsd_scraper = NsdScraper(
            config=self.config,
            logger=self.logger,
            data_cleaner=self.data_cleaner,
            worker_pool_executor=self.worker_pool_executor,
            metrics_collector=self.collector,
            repository=nsd_repo,
            http_client=self.http_client,
        )
        nsd_service = NsdService(
            config=self.config,
            logger=self.logger,
            repository=nsd_repo,
            company_repo=company_repo,
            scraper=nsd_scraper,
        )

        nsd_service.sync_nsd()

    def _statement_service(self) -> None:
        """Build and execute the financial statement pipeline."""
        company_repo = self.company_repo
        nsd_repo = SqlAlchemyNsdRepository(
            database_url=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        raw_statement_repo = SqlAlchemyRawStatementRepository(
            database_url=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        parsed_statement_repo = SqlAlchemyParsedStatementRepository(
            database_url=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )

        raw_statements_scraper = RawStatementScraper(
            config=self.config,
            logger=self.logger,
            data_cleaner=self.data_cleaner,
            metrics_collector=self.collector,
            http_client=self.http_client,
            worker_pool_executor=self.worker_pool_executor,
        )

        fetch_processor = FetchStatementsProcessor(
            logger=self.logger,
            config=self.config,
            source=raw_statements_scraper,
            company_repo=company_repo,
            nsd_repo=nsd_repo,
            raw_statement_repo=raw_statement_repo,
            parsed_statements_repo=parsed_statement_repo,
            metrics_collector=self.collector,
            worker_pool_executor=self.worker_pool_executor,
        )
        # raw_rows = fetch_processor.run()

        parse_pool = WorkerPool(
            config=self.config,
            metrics_collector=self.collector,
            max_workers=self.config.global_settings.max_workers or 1,
        )

        parse_processor = ParseStatementsProcessor(
            logger=self.logger,
            repository=parsed_statement_repo,
            config=self.config,
            worker_pool_executor=parse_pool,
            metrics_collector=self.collector,
            max_workers=self.config.global_settings.max_workers or 1,
        )

        raw_rows = self._load_transformed()  # mock
        parsed_groups = parse_processor.run(raw_rows)

        transform_processor = TransformStatementsProcessor(
            config=self.config,
            logger=self.logger,
            parsed_repo=parsed_statement_repo,
        )
        transform_processor.run(parsed_groups)

    def _load_transformed(self):
        from typing import  Dict, List, Tuple
        from collections import defaultdict
        from domain.dto import NsdDTO
        from domain.dto.raw_statement_dto import RawStatementDTO

        raw_statement_repo = SqlAlchemyRawStatementRepository(
            database_url=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )

        nsd_repo = SqlAlchemyNsdRepository(
            database_url=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        company_names = [company.company_name for company in self.company_repo.iter_all()]
        company_name = '2W ECOBANK SA'

        raw_statements = raw_statement_repo.get_by_company_name(company_name=company_name)

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
        criteria: str | List = 'company_name'
        values: str | List[str | List] = company_name
        nsd_index = {n.nsd: n for n in nsd_repo.get_by_column_values('company_name', values)}
        
        # 4) monta os pares apenas quando existir NsdDTO correspondente
        pairs: List[Tuple[NsdDTO, List[RawStatementDTO]]] = [
            (nsd_index[nsd_id], rows)
            for nsd_id, rows in buckets.items()
            if nsd_id in nsd_index
        ]

        # 5) ordena como no _build_targets para previsibilidade
        pairs.sort(key=lambda p: (p[0].company_name or "", p[0].quarter, p[0].version))

        return pairs
    
