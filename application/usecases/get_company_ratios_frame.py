from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from application.dtos.company_ratios_frame_dto import CompanyRatiosFrameDTO
from application.services.cache_ratios_service import CacheRatiosService
import domain.utils.intel as intel

from application.utils.ratios_pipeline import (
    create_ratios,
    load_indicators,
    load_quotes,
    load_statements,
    treat_data,
    treat_indicators,
)
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from domain.exceptions import DomainError
from domain.ports.cache_ratios_port import CacheRatiosPort
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.value_objects import SearchFilterTree


@dataclass(frozen=True)
class GetCompanyRatiosFrameRequest:
    company_name: str
    filters: Optional[SearchFilterTree] = None


@dataclass
class GetCompanyRatiosFrameUseCase:
    config: ConfigPort
    logger: LoggerPort
    repository_stock_quote: RepositoryStockQuotePort
    repository_indicators: RepositoryIndicatorsPort
    repository_statements_fetched: RepositoryStatementFetchedPort
    cache_ratios: CacheRatiosPort
    companies_eligible_port: CompaniesEligiblePort
    uow_factory: UowFactoryPort

    def __post_init__(self) -> None:
        self._cache_service = CacheRatiosService(
            cache_port=self.cache_ratios,
            logical_name=self.config.fly_settings.app_name,
            version=self.config.fly_settings.version,
        )
        self._ratios_code_hash = CacheRatiosService.build_code_hash([create_ratios, intel])

    def __call__(self, request: GetCompanyRatiosFrameRequest) -> CompanyRatiosFrameDTO:
        return self.run(request)

    def run(self, request: GetCompanyRatiosFrameRequest) -> CompanyRatiosFrameDTO:
        company_name = (request.company_name or "").strip()
        if not company_name:
            raise DomainError("company_name is required to fetch ratios")

        with self.uow_factory() as uow:
            eligible = self.companies_eligible_port.list(
                uow=uow,
                company_name=company_name,
            )
            if not eligible:
                raise DomainError(f"Company '{company_name}' is not eligible for ratios computation")

            company_dto = eligible[0]
            ticker_codes = list(company_dto.ticker_codes or [])

            raw_indicators = load_indicators(self.repository_indicators, uow=uow)
            treated_indicators = {
                key: treat_indicators(df.copy())
                for key, df in raw_indicators.items()
            }
            statements = load_statements(
                self.repository_statements_fetched,
                company_name=company_dto.company_name or company_name,
                uow=uow,
            )
            quotes = load_quotes(
                self.repository_stock_quote,
                ticker_codes,
                uow=uow,
            )
            uow.commit()

        snapshot = {
            "indicators": treated_indicators,
            "statements": statements,
            "quotes": quotes,
        }

        company_data = treat_data(snapshot, aggregate_method="last")

        def compute_fn() -> pd.DataFrame:
            return create_ratios(company_data)

        frame, cache_result = self._cache_service.get_or_compute(
            company_name=company_dto.company_name or company_name,
            quotes=company_data.get("quotes"),
            statements=company_data.get("statements"),
            indicators=company_data.get("indicators"),
            compute_fn=compute_fn,
            code_hash=self._ratios_code_hash,
            filters=request.filters,
        )

        ticker = ticker_codes[0] if ticker_codes else None
        meta = {
            "filters": request.filters.to_dict() if request.filters else None,
        }

        return CompanyRatiosFrameDTO(
            company_name=company_dto.company_name or company_name,
            ticker=ticker,
            frame=frame,
            cache_info=cache_result,
            meta=meta,
        )
