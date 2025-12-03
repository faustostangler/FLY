from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Body, Depends

from application.usecases.get_company_facets import GetCompanyFacetsUseCase
from application.usecases.search_companies import SearchCompaniesUseCase
from domain.value_objects.company_filters import (
    CompanyFilterClause,
    CompanyFilterCondition,
    CompanyFilterQuery,
    CompanyField,
    ComparisonOperator,
    LogicalOperator,
)
from presentation.backend.dependencies.company_facets_dependencies import (
    get_company_facets_usecase,
)
from presentation.backend.dependencies.company_search_dependencies import (
    get_company_search_usecase,
)
from presentation.backend.dto.company_facets_dto import CompanyFacetsResponseDTO
from presentation.backend.dto.company_search_dto import (
    CompanyFilterConditionDTO,
    CompanyFilterQueryDTO,
    CompanySearchResponseDTO,
)


router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/search", response_model=CompanySearchResponseDTO)
async def search_companies(
    filters: CompanyFilterQueryDTO = Body(default_factory=CompanyFilterQueryDTO),
    use_case: SearchCompaniesUseCase = Depends(get_company_search_usecase),
) -> CompanySearchResponseDTO:
    query = _map_to_domain(filters)
    result = use_case(query=query)
    return CompanySearchResponseDTO(**asdict(result))


@router.get("/facets", response_model=CompanyFacetsResponseDTO)
async def get_company_facets(
    use_case: GetCompanyFacetsUseCase = Depends(get_company_facets_usecase),
) -> CompanyFacetsResponseDTO:
    result = use_case()
    return CompanyFacetsResponseDTO(**asdict(result))


def _map_to_domain(dto: CompanyFilterQueryDTO | None) -> CompanyFilterQuery:
    if dto is None:
        return CompanyFilterQuery()

    clauses: list[CompanyFilterClause] = []
    for clause in dto.clauses:
        logical = _map_logical(clause.logical)
        if logical is None:
            continue
        condition = _map_condition(clause.condition)
        group = _map_to_domain(clause.group) if clause.group else None

        if group is not None and not group.clauses:
            group = None

        if condition is None and group is None:
            continue

        try:
            clauses.append(
                CompanyFilterClause(
                    logical=logical,
                    condition=condition,
                    group=group,
                )
            )
        except ValueError:
            continue
    return CompanyFilterQuery(clauses=clauses)


def _map_logical(value: str | None) -> LogicalOperator | None:
    if not value:
        return LogicalOperator.AND
    try:
        normalized = value.strip().upper()
        aliases = {
            "MUST": LogicalOperator.AND,
            "SHOULD": LogicalOperator.OR,
            "MUST_NOT": LogicalOperator.NOT,
            "SHOULD_NOT": LogicalOperator.NOT,
            "OR-NOT": LogicalOperator.NOT,
            "OR_NOT": LogicalOperator.NOT,
        }
        if normalized in aliases:
            return aliases[normalized]
        return LogicalOperator(normalized)
    except ValueError:
        return None


def _map_condition(
    condition_dto: CompanyFilterConditionDTO | None,
) -> CompanyFilterCondition | None:
    if condition_dto is None:
        return None
    field_value = (condition_dto.field or "").strip()
    if not field_value:
        return None
    try:
        field = CompanyField(field_value)
    except ValueError:
        return None

    operator_value = (condition_dto.operator or "IN").strip().upper()
    if operator_value == "OR_NOT":  # guard legacy inputs
        operator_value = "IN"
    try:
        operator = ComparisonOperator(operator_value)
    except ValueError:
        return None

    values = [str(v) for v in (condition_dto.values or []) if str(v).strip()]
    return CompanyFilterCondition(field=field, operator=operator, values=values)
