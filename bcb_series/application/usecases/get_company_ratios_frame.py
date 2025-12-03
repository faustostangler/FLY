from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from application.dtos.company_ratios_frame_dto import CompanyRatiosFrameDTO
from application.processors.filter_builder import FilterBuilder
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.usecases.normalize_ratios import NormalizeUseCase
from domain import DomainError
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.cache_ratios_port import CacheRatiosPort
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.value_objects import SearchFilterTree
from infrastructure.utils.pandas_visitor import PandasVisitor


ALLOWED_RATIO_FILTER_FIELDS: set[str] = {
    "date",
}


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
    worker_pool: WorkerPoolPort

    def __post_init__(self) -> None:
        self._normalize_usecase = NormalizeUseCase(
            config=self.config,
            logger=self.logger,
            repository_stock_quote=self.repository_stock_quote,
            repository_indicators=self.repository_indicators,
            repository_statements_fetched=self.repository_statements_fetched,
            cache_ratios=self.cache_ratios,
            companies_eligible_port=self.companies_eligible_port,
            uow_factory=self.uow_factory,
            worker_pool=self.worker_pool,
        )

    def __call__(
        self,
        *,
        company_name: str,
        filters: Optional[SearchFilterTree] = None,
    ) -> CompanyRatiosFrameDTO:
        return self.run(company_name=company_name, filters=filters)

    def run(
        self,
        *,
        company_name: str,
        filters: Optional[SearchFilterTree] = None,
    ) -> CompanyRatiosFrameDTO:
        target_name = (company_name or "").strip()
        if not target_name:
            raise DomainError("company_name é obrigatório para recuperar ratios.")

        company = self._get_company(target_name)

        treated_indicators = self._load_treated_indicators()

        with self.uow_factory() as uow:
            quotes = self._normalize_usecase._load_quotes(  # pylint: disable=protected-access
                ticker_codes=list(company.ticker_codes),
                uow=uow,
            )
            statements = self._normalize_usecase._load_statements(  # pylint: disable=protected-access
                company_name=company.company_name or target_name,
                uow=uow,
            )

        data_snapshot = {
            "indicators": treated_indicators,
            "statements": statements,
            "quotes": quotes,
        }

        company_data = self._normalize_usecase._treat_data(  # pylint: disable=protected-access
            data_snapshot,
            aggregate_method="last",
        )

        def _compute() -> pd.DataFrame:
            return self._normalize_usecase._create_ratios(company_data)  # pylint: disable=protected-access

        df, cache_result = self._normalize_usecase.cache_ratios_service.get_or_compute(
            company_name=company.company_name or target_name,
            quotes=company_data.get("quotes"),
            statements=company_data.get("statements"),
            indicators=company_data.get("indicators"),
            compute_fn=_compute,
            code_hash=self._normalize_usecase.ratios_code_hash,
        )

        effective_filters: Optional[SearchFilterTree] = None
        if filters is not None and not filters.is_empty():
            effective_filters = filters.filtered_by_fields(ALLOWED_RATIO_FILTER_FIELDS)

        df = self._apply_filters(df, effective_filters)

        ticker = next(iter(company.ticker_codes), None)
        meta = {
            "company_id": company.id,
            "filters": effective_filters.to_dict() if effective_filters else None,
        }

        return CompanyRatiosFrameDTO(
            company_name=company.company_name or target_name,
            frame=df,
            cache_info=cache_result,
            ticker=ticker,
            meta=meta,
        )

    def _apply_filters(
        self,
        df: pd.DataFrame,
        filters: Optional[SearchFilterTree],
    ) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        if filters is None or filters.is_empty():
            return df

        try:
            spec = FilterBuilder().build_spec(filters.to_dict())
            mask = spec.accept(PandasVisitor(), df)
            return df.loc[mask].copy()
        except Exception as exc:  # pragma: no cover - defensive branch
            if self.logger:
                self.logger.warning(
                    "Falha ao aplicar filtros em GetCompanyRatiosFrameUseCase: %s",
                    exc,
                )
            return df

    def _load_treated_indicators(self) -> dict[str, dict[str, pd.DataFrame]]:
        with self.uow_factory() as uow:
            indicators = self._normalize_usecase._load_indicators(uow=uow)  # pylint: disable=protected-access
        return {
            indicator: self._normalize_usecase._treat_indicators(df)  # pylint: disable=protected-access
            for indicator, df in indicators.items()
        }

    def _get_company(self, company_name: str) -> CompanyEligibleDTO:
        with self.uow_factory() as uow:
            matches = self.companies_eligible_port.list(
                uow=uow,
                company_name=company_name,
            )
        if not matches:
            raise DomainError(
                f"Empresa '{company_name}' não encontrada na projeção de elegíveis."
            )
        return matches[0]

