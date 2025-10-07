from typing import Any, List

from datetime import date, datetime, timedelta
from typing import Tuple

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.scraper_indicators_port import ScraperIndicatorsPort

from infrastructure.utils.list_flatenner import ListFlattener

# from infrastructure.helpers.list_flattener import ListFlattener


class SyncBCBIndicatorUseCase:
    """Use case for synchronizing data between scraper and repository."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_indicators: RepositoryIndicatorsPort,
        scraper_indicators: ScraperIndicatorsPort,

        uow_factory: UowFactoryPort,

        max_workers: int = 1,
    ):
        """Initialize the use case with its dependencies.

        Args:
            config (ConfigPort): Application configuration provider.
            logger (LoggerPort): Logger interface for capturing messages.
            repository (RepositoryCompanyDataPort): Repository for persisting company data.
            scraper (ScraperCompanyDataPort): Scraper used to fetch company data.
            max_workers (int, optional): Maximum number of workers for parallel execution.
                Defaults to 1, or falls back to the value in the config worker pool.
        """
        self.config = config
        self.logger = logger
        self.repository_indicators = repository_indicators
        self.scraper_indicators = scraper_indicators
        self.uow_factory = uow_factory

        self.max_workers = max_workers or (self.config.worker_pool.max_workers or 1)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.run()

    def run(self) -> SyncResultsDTO:
        """Run the full synchronization pipeline.

        Steps:
            1. Retrieve company data from the scraper.
            2. Transform results into ``CompanyDataDTO`` objects.
            3. Save them into the repository in batches.

        Returns:
            SyncCompanyDataResultDTO: Summary of the synchronization process,
            including counts and network usage metrics.
        """
        # Collect company identifiers already stored in the repository
        results: list[IndicatorRecordDTO] = []
        existing_codes: List[Tuple[str, str, datetime | None, datetime]] = []
        today = datetime.today()
        default_start_date = datetime.strptime("01/01/1900", "%d/%m/%Y")
        try:
            with self.uow_factory() as uow:
                sources: List[Tuple[str, str]] = self.config.indicators.source["bcb"]
                for (name, code_series) in sources:
                    last_date = self.repository_indicators.get_last_date(
                        source="BCB", code=code_series, uow=uow
                    )

                    last_datetime: datetime | None = None
                    if isinstance(last_date, datetime):
                        last_datetime = last_date
                    elif isinstance(last_date, date):
                        last_datetime = datetime.combine(
                            last_date, datetime.min.time()
                        )

                    if last_datetime is not None:
                        start_date = last_datetime + timedelta(days=1)
                    else:
                        start_date = default_start_date

                    if start_date > today:
                        continue

                    existing_codes.append((name, code_series, start_date, today))
                # Fetch from scraper and persist them in batch mode
                results = self.scraper_indicators.fetch_all(existing_codes=existing_codes, save_callback=self._save_batch)

        except Exception as e:
            self.logger.log(f"Erro {e}")

        return SyncResultsDTO(items=results, metrics=self.scraper_indicators.get_metrics())

    def _save_batch(
        self,
        items: list[IndicatorRecordDTO],
        *,
        uow: Uow | None = None,
    ) -> None:
        """Transform and persist a batch of company data.

        Args:
            buffer (List[CompanyDataDTO]): Raw or nested DTOs retrieved by the scraper.
        """
        # type narrowing
        if uow is None:
            raise RuntimeError("SaveCallback chamado sem UoW")

        # Flatten potential nested lists from scraper output
        flat_items = ListFlattener.flatten(items)

        # Convert raw scraper DTOs into domain-level DTOs
        dtos = [IndicatorRecordDTO.from_raw(item) for item in flat_items]

        # Persist the transformed DTOs in bulk
        self.repository_indicators.save_all(dtos, uow=uow)
