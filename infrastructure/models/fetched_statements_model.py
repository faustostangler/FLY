from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dtos.fetched_statement_dto import StatementFetchedDTO

from infrastructure.models.base_statements_model import BaseStatementModel


class StatementFetchedModel(BaseStatementModel):
    """ORM model for fetched statement rows."""

    __tablename__ = "tbl_fetched_statements"

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
            name="uq_fetched_statements_fullkey",
        ),
        Index("ix_fetched_statements_company_name", "company_name"),
        Index("ix_fetched_statements_quarter", "quarter"),
        Index("ix_fetched_statements_account", "account"),
        Index("ix_fetched_statements_nsd", "nsd"),
        Index("ix_fetched_statements_company_name_quarter", "company_name", "quarter"),
    )

    processing_hash: Mapped[str | None] = mapped_column(String, index=True)

    _FIELDS = BaseStatementModel._FIELDS + ("processing_hash",)

    @staticmethod
    def from_dto(dto: StatementFetchedDTO) -> "StatementFetchedModel":
        return StatementFetchedModel(**StatementFetchedModel._kwargs_from_dto(dto))

    def to_dto(self) -> StatementFetchedDTO:
        return StatementFetchedDTO(**self._dto_kwargs())
