"""Use case that refreshes the eligible companies projection from source snapshots."""

from __future__ import annotations

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.services.eligible_companies_batch_updater_service import (
    EligibleCompaniesBatchUpdaterService,
)
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort


class CompaniesEligibleUseCase:
    """Coordinates the refresh of the eligible companies read-model."""

    def __init__(
        self,
        *,
        logger: LoggerPort,
        repository_company: RepositoryCompanyDataPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        repository_stock_quote: RepositoryStockQuotePort,
        batch_service: EligibleCompaniesBatchUpdaterService,
        uow_factory: UowFactoryPort,
    ) -> None:
        self._logger = logger
        self._repository_company = repository_company
        self._repository_statements_fetched = repository_statements_fetched
        self._repository_stock_quote = repository_stock_quote
        self._batch_service = batch_service
        self._uow_factory = uow_factory

    def __call__(self) -> list[CompanyEligibleDTO]:
        return self.run()

    def run(self) -> list[CompanyEligibleDTO]:
        """Refresh the projection in a single transaction."""

        with self._uow_factory() as uow:
            companies = self._repository_company.get_all(uow=uow)
            statement_names = self._repository_statements_fetched.get_unique_by_column(
                column_name="company_name",
                uow=uow,
            )
            quote_tickers = self._repository_stock_quote.get_unique_by_column(
                column_name="ticker",
                uow=uow,
            )

            eligible_companies = self._batch_service.rebuild(
                uow=uow,
                companies=companies,
                statement_company_names=statement_names,
                quote_tickers=quote_tickers,
            )

            uow.commit()
            # self._logger.log(
            #     f"Eligible companies projection refreshed: {len(eligible_companies)} items",
            #     level="info",
            # )

            return eligible_companies
