"""Application service responsible for rebuilding the eligible companies projection."""

from __future__ import annotations

from typing import Collection, Iterable, Sequence

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

        for company in companies:
            name = (company.company_name or "").strip()
            if not name:
                continue

            if name in seen_names:
                continue
            seen_names.add(name)

            is_valid, normalized_tickers, reason = decide_valid_company(
                has_statements=name in statement_set,
                candidate_tickers=company.ticker_codes or [],
                available_quote_tickers=quote_set,
            )

            if not is_valid:
                continue

            entity = EligibleCompany(
                company_name=name,
                cvm_code=company.cvm_code,
                ticker_codes=normalized_tickers,
                reason=reason,
                trading_name=company.trading_name,
                industry_sector=company.industry_sector,
                industry_subsector=company.industry_subsector,
                industry_segment=company.industry_segment,
                company_segment=company.company_segment,
            )

            projection.append(CompanyEligibleDTO.from_entity(entity))

        self._port.replace_all(projection, uow=uow)
        self._logger.log(
            f"Eligible companies projection updated with {len(projection)} entries",
            level="info",
        )

        return projection
