"""Application service responsible for rebuilding the eligible companies projection."""

from __future__ import annotations

from typing import Collection, Iterable, Sequence
import time

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.entities import EligibleCompany
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.services.valid_company_rules import decide_valid_company


class EligibleCompaniesBatchUpdaterService:
    """Coordinates transformation from raw snapshots into the read-model DTOs."""

    def __init__(
        self,
        *,
        logger: LoggerPort,
        port: CompaniesEligiblePort,
    ) -> None:
        self._logger = logger
        self._port = port

    def rebuild(
        self,
        *,
        uow: Uow,
        companies: Sequence[CompanyDataDTO],
        statement_company_names: Collection[str],
        quote_tickers: Iterable[str],
    ) -> list[CompanyEligibleDTO]:
        """Recompute the eligible companies projection and persist it."""

        statement_set = {name for name in statement_company_names if name}
        quote_set = {str(t).strip().upper() for t in quote_tickers if t}

        projection: list[CompanyEligibleDTO] = []
        seen_names: set[str] = set()

        start_time = time.perf_counter()
        for i, company in enumerate(companies):
            name = (company.company_name or "").strip()
            if not name:
                continue

            if name in seen_names:
                continue
            seen_names.add(name)

            # progress = {
            #     "index": i,
            #     "size": len(companies),
            #     "start_time": start_time,
            # }
            # extra_info = {
            #     "company_name": name,
            # }
            # self._logger.log(
            #     f"{company.cvm_code}, {company.company_name}",
            #     level="info",
            #     progress=progress,
            #     extra=extra_info,
            # )

            is_valid, normalized_tickers, reason = decide_valid_company(
                has_statements=name in statement_set,
                candidate_tickers=company.ticker_codes or [],
                available_quote_tickers=quote_set,
            )

            if not is_valid:
                continue

            entity = EligibleCompany(
                id=company.id,
                company_name=name,
                cvm_code=company.cvm_code,
                issuing_company=company.issuing_company,
                trading_name=company.trading_name,
                cnpj=company.cnpj,
                ticker_codes=normalized_tickers,
                isin_codes=tuple(company.isin_codes or []),
                other_codes=tuple(company.other_codes or []),
                market=company.market,
                reason=reason,
                industry_sector=company.industry_sector,
                industry_subsector=company.industry_subsector,
                industry_segment=company.industry_segment,
                industry_classification=company.industry_classification,
                industry_classification_eng=company.industry_classification_eng,
                activity=company.activity,
                company_segment=company.company_segment,
                company_segment_eng=company.company_segment_eng,
                company_category=company.company_category,
                company_type=company.company_type,
                listing_segment=company.listing_segment,
                registrar=company.registrar,
                website=company.website,
                institution_common=company.institution_common,
                institution_preferred=company.institution_preferred,
                status=company.status,
                market_indicator=company.market_indicator,
                code=company.code,
                has_bdr=company.has_bdr,
                type_bdr=company.type_bdr,
                has_quotation=company.has_quotation,
                has_emissions=company.has_emissions,
                date_quotation=company.date_quotation,
                last_date=company.last_date,
                listing_date=company.listing_date,
            )

            projection.append(CompanyEligibleDTO.from_entity(entity))

        self._port.replace_all(projection, uow=uow)
        # self._logger.log(
        #     f"Eligible companies projection updated with {len(projection)} entries",
        #     level="info",
        # )

        return projection
