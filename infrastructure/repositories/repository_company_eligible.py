"""Repository implementing the eligible companies read/write ports."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from sqlalchemy import and_, delete, func, not_, or_, select
from sqlalchemy.orm import Session

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.value_objects.company_filters import (
    CompanyFilterClause,
    CompanyFilterCondition,
    CompanyFilterQuery,
    CompanyField,
    ComparisonOperator,
    LogicalOperator,
)
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.models.company_eligible_model import CompanyEligibleModel


class RepositoryCompanyEligible(
    RepositoryBase[CompanyEligibleDTO, str],
    CompaniesEligiblePort,
):
    """SQLite-backed repository for the eligible companies projection."""

    def __init__(self, *, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config, logger)
        self._config = config
        self._logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the ORM model class and primary key tuple used by this repository.

        Returns:
            Tuple[type, tuple]: A tuple of (model class, primary key columns).
        """
        # Provide the bound model and its primary key columns
        return CompanyEligibleModel, (CompanyEligibleModel.cvm_code,)

    # # Se o seu RepositoryBase também pede mapeamento DTO<->Model, exponha:
    # def to_model(self, dto: CompanyEligibleDTO) -> CompanyEligibleModel:  # opcional, se o base chamar
    #     return CompanyEligibleModel.from_dto(dto)

    # def to_dto(self, model: CompanyEligibleModel) -> CompanyEligibleDTO:  # opcional, se o base chamar
    #     return model.to_dto()

    def list(
        self,
        *,
        uow: Uow,
        cvm_code: str | None = None,
        company_name: str | None = None,
        segment: str | None = None,
    ) -> list[CompanyEligibleDTO]:
        session: Session = uow.session
        query = session.query(CompanyEligibleModel)

        if cvm_code:
            query = query.filter(CompanyEligibleModel.cvm_code == cvm_code)

        if company_name:
            like = f"%{company_name}%"
            query = query.filter(CompanyEligibleModel.company_name.ilike(like))

        if segment:
            like = f"%{segment}%"
            query = query.filter(
                (CompanyEligibleModel.company_segment.ilike(like))
                | (CompanyEligibleModel.industry_segment.ilike(like))
            )

        query = query.order_by(CompanyEligibleModel.company_name)
        rows = query.all()

        return [row.to_dto() for row in rows]

    def search(
        self,
        *,
        uow: Uow,
        query: CompanyFilterQuery,
        limit: int | None = None,
    ) -> list[CompanyEligibleDTO]:
        session: Session = uow.session
        model = CompanyEligibleModel

        stmt = select(model)
        expression = self._build_boolean_expression(query.clauses, model)
        if expression is not None:
            stmt = stmt.where(expression)

        stmt = stmt.order_by(model.company_name)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = session.execute(stmt)
        rows = result.scalars().all()
        return [row.to_dto() for row in rows]

    def _build_boolean_expression(
        self,
        clauses: Sequence[CompanyFilterClause],
        model: type[CompanyEligibleModel],
    ) -> Optional[object]:
        if not clauses:
            return None

        must: list[object] = []
        should: list[object] = []
        negatives: list[object] = []

        for clause in clauses:
            if clause.is_group():
                inner_expression = self._build_boolean_expression(
                    clause.group.clauses if clause.group else [],
                    model,
                )
            else:
                inner_expression = self._build_condition_expression(
                    clause.condition,
                    model,
                )

            if inner_expression is None:
                continue

            if clause.logical == LogicalOperator.AND:
                must.append(inner_expression)
            elif clause.logical == LogicalOperator.OR:
                should.append(inner_expression)
            elif clause.logical == LogicalOperator.NOT:
                negatives.append(inner_expression)

        return self._combine_boolean_expressions(must, should, negatives)

    def _combine_boolean_expressions(
        self,
        must: Sequence[object],
        should: Sequence[object],
        negatives: Sequence[object],
    ) -> Optional[object]:
        expression: Optional[object] = None

        if must:
            expression = and_(*must)

        if should:
            should_expr = should[0] if len(should) == 1 else or_(*should)
            expression = should_expr if expression is None else and_(expression, should_expr)

        if negatives:
            negative_exprs = [not_(expr) for expr in negatives]
            neg_expr = negative_exprs[0] if len(negative_exprs) == 1 else and_(*negative_exprs)
            expression = neg_expr if expression is None else and_(expression, neg_expr)

        return expression

    def _build_condition_expression(
        self,
        condition: CompanyFilterCondition | None,
        model: type[CompanyEligibleModel],
    ) -> Optional[object]:
        if condition is None:
            return None

        column = self._map_field_to_column(condition.field, model)
        if column is None:
            return None

        if condition.field in self._boolean_fields():
            bool_values = [self._parse_boolean(value) for value in condition.values]
            bool_values = [value for value in bool_values if value is not None]
            if not bool_values:
                return None

            if condition.operator in (ComparisonOperator.EQUALS, ComparisonOperator.IN):
                if condition.operator is ComparisonOperator.EQUALS:
                    target = bool_values[0]
                    return column.is_(target) if target is None else column == target
                return column.in_(bool_values)
            return None

        values = [value for value in condition.values if isinstance(value, str) and value.strip()]

        if not values and condition.operator not in (
            ComparisonOperator.CONTAINS,
            ComparisonOperator.STARTS_WITH,
        ):
            return None

        if condition.operator == ComparisonOperator.EQUALS:
            lowered = [value.lower() for value in values]
            if len(lowered) == 1:
                return func.lower(column) == lowered[0]
            return func.lower(column).in_(lowered)

        if condition.operator == ComparisonOperator.IN:
            lowered = [value.lower() for value in values]
            return func.lower(column).in_(lowered)

        if condition.operator == ComparisonOperator.CONTAINS:
            expressions = [
                func.lower(column).like(f"%{value.lower()}%")
                for value in values or [""]
            ]
            return or_(*expressions) if expressions else None

        if condition.operator == ComparisonOperator.STARTS_WITH:
            expressions = [
                func.lower(column).like(f"{value.lower()}%")
                for value in values or [""]
            ]
            return or_(*expressions) if expressions else None

        return None

    def _map_field_to_column(
        self,
        field: CompanyField,
        model: type[CompanyEligibleModel],
    ):
        mapping = {
            CompanyField.COMPANY_NAME: model.company_name,
            CompanyField.TRADING_NAME: model.trading_name,
            CompanyField.ISSUING_COMPANY: model.issuing_company,
            CompanyField.CNPJ: model.cnpj,
            CompanyField.CVM_CODE: model.cvm_code,
            CompanyField.MARKET: model.market,
            CompanyField.INDUSTRY_SECTOR: model.industry_sector,
            CompanyField.INDUSTRY_SUBSECTOR: model.industry_subsector,
            CompanyField.INDUSTRY_SEGMENT: model.industry_segment,
            CompanyField.INDUSTRY_CLASSIFICATION: model.industry_classification,
            CompanyField.INDUSTRY_CLASSIFICATION_ENG: model.industry_classification_eng,
            CompanyField.COMPANY_CATEGORY: model.company_category,
            CompanyField.COMPANY_TYPE: model.company_type,
            CompanyField.LISTING_SEGMENT: model.listing_segment,
            CompanyField.REGISTRAR: model.registrar,
            CompanyField.INSTITUTION_COMMON: model.institution_common,
            CompanyField.INSTITUTION_PREFERRED: model.institution_preferred,
            CompanyField.STATUS: model.status,
            CompanyField.MARKET_INDICATOR: model.market_indicator,
            CompanyField.CODE: model.code,
            CompanyField.TYPE_BDR: model.type_bdr,
            CompanyField.HAS_BDR: model.has_bdr,
            CompanyField.HAS_QUOTATION: model.has_quotation,
            CompanyField.HAS_EMISSIONS: model.has_emissions,
        }
        return mapping.get(field)

    @staticmethod
    def _boolean_fields() -> set[CompanyField]:
        return {
            CompanyField.HAS_BDR,
            CompanyField.HAS_QUOTATION,
            CompanyField.HAS_EMISSIONS,
        }

    @staticmethod
    def _parse_boolean(value: str | bool | None) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y", "sim"}:
            return True
        if normalized in {"false", "0", "no", "n", "nao", "não"}:
            return False
        return None

    def replace_all(
        self,
        items: Sequence[CompanyEligibleDTO],
        *,
        uow: Uow,
    ) -> None:
        session: Session = uow.session

        session.execute(delete(CompanyEligibleModel))

        if items:
            objects = [CompanyEligibleModel.from_dto(item) for item in items]
            session.bulk_save_objects(objects)

        # self._logger.log(
        #     f"Projection tbl_company_eligible replaced with {len(items)} rows",
        #     level="debug",
        # )
