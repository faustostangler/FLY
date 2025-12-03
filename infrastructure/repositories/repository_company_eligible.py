"""Repository implementing the eligible companies read/write ports."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from sqlalchemy import and_, delete, func, not_, or_
from sqlalchemy.orm import Session

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.ports.repository_company_eligible_port import RepositoryCompanyEligiblePort
from domain.value_objects.company_filters import (
    CompanyFilterClause,
    CompanyFilterCondition,
    CompanyFilterQuery,
    CompanyField,
    ComparisonOperator,
    LogicalOperator,
)
from infrastructure.models.company_eligible_model import CompanyEligibleModel
from infrastructure.repositories.repository_base import RepositoryBase

DEFAULT_LIMIT = 200

STRING_FIELDS: set[CompanyField] = {
    CompanyField.ISSUING_COMPANY,
    CompanyField.TRADING_NAME,
    CompanyField.COMPANY_NAME,
    CompanyField.CNPJ,
    CompanyField.MARKET,
    CompanyField.INDUSTRY_SECTOR,
    CompanyField.INDUSTRY_SUBSECTOR,
    CompanyField.INDUSTRY_SEGMENT,
    CompanyField.INDUSTRY_CLASSIFICATION,
    CompanyField.INDUSTRY_CLASSIFICATION_ENG,
    CompanyField.ACTIVITY,
    CompanyField.COMPANY_SEGMENT,
    CompanyField.COMPANY_SEGMENT_ENG,
    CompanyField.COMPANY_CATEGORY,
    CompanyField.COMPANY_TYPE,
    CompanyField.LISTING_SEGMENT,
    CompanyField.REGISTRAR,
    CompanyField.WEBSITE,
    CompanyField.INSTITUTION_COMMON,
    CompanyField.INSTITUTION_PREFERRED,
    CompanyField.STATUS,
    CompanyField.MARKET_INDICATOR,
    CompanyField.CODE,
    CompanyField.TYPE_BDR,
    CompanyField.REASON,
}

BOOLEAN_FIELDS: set[CompanyField] = {
    CompanyField.HAS_BDR,
    CompanyField.HAS_QUOTATION,
    CompanyField.HAS_EMISSIONS,
}

DATE_FIELDS: set[CompanyField] = {
    CompanyField.DATE_QUOTATION,
    CompanyField.LAST_DATE,
    CompanyField.LISTING_DATE,
}


class RepositoryCompanyEligible(
    RepositoryBase[CompanyEligibleDTO, str],
    CompaniesEligiblePort,
    RepositoryCompanyEligiblePort,
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

    # ------------------------------------------------------------------
    # Query builder support
    # ------------------------------------------------------------------
    def search(
        self,
        query: CompanyFilterQuery,
        *,
        uow: Uow,
        limit: int | None = None,
    ) -> list[CompanyEligibleDTO]:
        session: Session = uow.session
        model, _ = self.get_model_class()

        stmt = session.query(model)

        expression = self._build_boolean_expression(query.clauses, model)
        if expression is not None:
            stmt = stmt.filter(expression)

        stmt = stmt.order_by(model.company_name.asc())

        # if limit is None:
        #     limit = DEFAULT_LIMIT
        if limit:
            stmt = stmt.limit(limit)

        rows = stmt.all()
        return [row.to_dto() for row in rows]

    def get_all(
        self,
        *,
        uow: Uow,
        batch_size: int | None = None,
    ) -> List[CompanyEligibleDTO]:
        session: Session = uow.session
        size = batch_size or self.config.repository.batch_size or 50

        query = (
            session.query(CompanyEligibleModel)
            .order_by(CompanyEligibleModel.company_name.asc())
        )

        results: List[CompanyEligibleDTO] = []
        offset = 0
        while True:
            chunk = query.offset(offset).limit(size).all()
            if not chunk:
                break

            results.extend(row.to_dto() for row in chunk)
            offset += size

        return results

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

    # Helpers -----------------------------------------------------------------
    def _build_boolean_expression(
        self, clauses: list[CompanyFilterClause], model
    ) -> Optional[object]:
        if not clauses:
            return None

        must_clauses: list[object] = []
        should_clauses: list[object] = []
        negative_clauses: list[object] = []

        for clause in clauses:
            if clause.is_group():
                expression = self._build_boolean_expression(clause.group.clauses, model)
            else:
                expression = self._build_condition_expression(clause.condition, model)

            if expression is None:
                continue

            if clause.logical == LogicalOperator.AND:
                must_clauses.append(expression)
            elif clause.logical == LogicalOperator.OR:
                should_clauses.append(expression)
            elif clause.logical == LogicalOperator.NOT:
                negative_clauses.append(expression)

        return self._combine_boolean_expressions(
            must_clauses, should_clauses, negative_clauses
        )

    def _combine_boolean_expressions(
        self,
        must_clauses: list[object],
        should_clauses: list[object],
        negative_clauses: list[object],
    ) -> Optional[object]:
        expression: Optional[object] = None

        if must_clauses:
            expression = and_(*must_clauses)

        if should_clauses:
            should_expr = (
                should_clauses[0]
                if len(should_clauses) == 1
                else or_(*should_clauses)
            )
            expression = (
                should_expr
                if expression is None
                else and_(expression, should_expr)
            )

        if negative_clauses:
            negatives = [not_(expr) for expr in negative_clauses]
            negative_expr = (
                negatives[0] if len(negatives) == 1 else and_(*negatives)
            )
            expression = (
                negative_expr
                if expression is None
                else and_(expression, negative_expr)
            )

        return expression

    def _build_condition_expression(
        self, condition: CompanyFilterCondition | None, model
    ) -> Optional[object]:
        if condition is None:
            return None

        column = self._map_field(condition.field, model)
        if column is None:
            return None

        if condition.field in DATE_FIELDS:
            return self._date_expression(condition, column)

        if condition.field in BOOLEAN_FIELDS:
            return self._boolean_expression(condition, column)

        return self._string_expression(condition, column)

    def _string_expression(self, condition: CompanyFilterCondition, column):
        values = [v for v in condition.values if v is not None]
        operator = condition.operator

        if not values and operator not in (
            ComparisonOperator.CONTAINS,
            ComparisonOperator.STARTS_WITH,
        ):
            return None

        if operator == ComparisonOperator.CONTAINS:
            return self._string_like(column, values, mode="contains")

        if operator == ComparisonOperator.STARTS_WITH:
            return self._string_like(column, values, mode="starts_with")

        lowered = [str(value).lower() for value in values]

        if operator == ComparisonOperator.EQUALS and len(lowered) == 1:
            value = lowered[0]
            return func.lower(column) == value

        if operator in (ComparisonOperator.EQUALS, ComparisonOperator.IN):
            return func.lower(column).in_(lowered)

        if not values:
            return None

        return func.lower(column).in_(lowered)

    def _string_like(self, column, values: list[str], *, mode: str):
        expressions = []
        targets = values or [""]
        for value in targets:
            pattern = str(value).lower()
            if mode == "contains":
                like_pattern = f"%{pattern}%"
            else:
                like_pattern = f"{pattern}%"
            expressions.append(func.lower(column).like(like_pattern))
        return or_(*expressions) if expressions else None

    def _boolean_expression(
        self, condition: CompanyFilterCondition, column
    ) -> Optional[object]:
        raw_values = condition.values or []
        normalized: list[bool] = []
        for value in raw_values:
            parsed = self._coerce_boolean(value)
            if parsed is not None:
                normalized.append(parsed)

        if not normalized:
            return None

        unique_values = list(dict.fromkeys(normalized))

        if condition.operator in (ComparisonOperator.IN, ComparisonOperator.EQUALS):
            if len(unique_values) == 1:
                return column.is_(unique_values[0])
            return column.in_(unique_values)

        return column.is_(unique_values[0])

    def _date_expression(
        self, condition: CompanyFilterCondition, column
    ) -> Optional[object]:
        values = condition.values or []
        if condition.operator != ComparisonOperator.BETWEEN or len(values) < 2:
            return None

        start = self._parse_date(values[0])
        end = self._parse_date(values[1])
        if not start or not end:
            return None
        if end < start:
            start, end = end, start
        return and_(column >= start, column <= end)

    @staticmethod
    def _parse_date(value: str | None):
        if not value:
            return None
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            return None

    @staticmethod
    def _coerce_boolean(value: object) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"true", "1", "yes", "sim"}:
            return True
        if text in {"false", "0", "no", "nao", "não"}:
            return False
        return None

    def _map_field(self, field: CompanyField, model):
        mapping = {
            CompanyField.ISSUING_COMPANY: model.issuing_company,
            CompanyField.TRADING_NAME: model.trading_name,
            CompanyField.COMPANY_NAME: model.company_name,
            CompanyField.CNPJ: model.cnpj,
            CompanyField.MARKET: model.market,
            CompanyField.INDUSTRY_SECTOR: model.industry_sector,
            CompanyField.INDUSTRY_SUBSECTOR: model.industry_subsector,
            CompanyField.INDUSTRY_SEGMENT: model.industry_segment,
            CompanyField.INDUSTRY_CLASSIFICATION: model.industry_classification,
            CompanyField.INDUSTRY_CLASSIFICATION_ENG: model.industry_classification_eng,
            CompanyField.ACTIVITY: model.activity,
            CompanyField.COMPANY_SEGMENT: model.company_segment,
            CompanyField.COMPANY_SEGMENT_ENG: model.company_segment_eng,
            CompanyField.COMPANY_CATEGORY: model.company_category,
            CompanyField.COMPANY_TYPE: model.company_type,
            CompanyField.LISTING_SEGMENT: model.listing_segment,
            CompanyField.REGISTRAR: model.registrar,
            CompanyField.WEBSITE: model.website,
            CompanyField.INSTITUTION_COMMON: model.institution_common,
            CompanyField.INSTITUTION_PREFERRED: model.institution_preferred,
            CompanyField.STATUS: model.status,
            CompanyField.MARKET_INDICATOR: model.market_indicator,
            CompanyField.CODE: model.code,
            CompanyField.TYPE_BDR: model.type_bdr,
            CompanyField.REASON: model.reason,
            CompanyField.HAS_BDR: model.has_bdr,
            CompanyField.HAS_QUOTATION: model.has_quotation,
            CompanyField.HAS_EMISSIONS: model.has_emissions,
            CompanyField.DATE_QUOTATION: model.date_quotation,
            CompanyField.LAST_DATE: model.last_date,
            CompanyField.LISTING_DATE: model.listing_date,
        }
        return mapping.get(field)
