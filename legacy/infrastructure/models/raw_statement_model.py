from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dto.statement_raw_dto import StatementRawDTO

from .abstract_statement_model import BaseStatementModel


class StatementRawModel(BaseStatementModel):
    """ORM model for raw statement rows."""

    __tablename__ = "tbl_raw_statements"

    nsd: Mapped[str] = mapped_column(
        String,
        ForeignKey("tbl_nsd.nsd"),
    )
    company_name: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("tbl_company.company_name"),
    )

    __table_args__ = (
        UniqueConstraint(
            "nsd",
            "company_name",
            "quarter",
            "version",
            "grupo",
            "quadro",
            "account",
            name="uq_raw_statements_fullkey",
        ),
        Index("ix_raw_statements_company_name", "company_name"),
        Index("ix_raw_statements_quarter", "quarter"),
        Index("ix_raw_statements_account", "account"),
        Index("ix_raw_statements_nsd", "nsd"),
        Index("ix_raw_statements_company_name_quarter", "company_name", "quarter"),
    )

    @staticmethod
    def from_dto(dto: StatementRawDTO) -> "StatementRawModel":
        return StatementRawModel(**StatementRawModel._kwargs_from_dto(dto))

    def to_dto(self) -> StatementRawDTO:
        return StatementRawDTO(**self._dto_kwargs())
