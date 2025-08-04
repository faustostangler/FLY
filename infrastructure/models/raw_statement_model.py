from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dto.raw_statement_dto import RawStatementDTO

from .abstract_statement_model import AbstractStatementModel


class RawStatementModel(AbstractStatementModel):
    """ORM model for raw statement rows."""

    __tablename__ = "tbl_raw_statements"

    nsd: Mapped[str] = mapped_column(
        String,
        ForeignKey("tbl_nsd.nsd"),
    )
    cvm_code: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("tbl_company.cvm_code"),
    )

    __table_args__ = (
        UniqueConstraint(
            "nsd",
            "cvm_code",
            "quarter",
            "version",
            "grupo",
            "quadro",
            "account",
            name="uq_raw_statements_fullkey",
        ),
        Index("ix_raw_statements_cvm_code", "cvm_code"),
        Index("ix_raw_statements_quarter", "quarter"),
        Index("ix_raw_statements_account", "account"),
        Index("ix_raw_statements_nsd", "nsd"),
        Index("ix_raw_statements_cvm_code_quarter", "cvm_code", "quarter"),
    )

    @staticmethod
    def from_dto(dto: RawStatementDTO) -> "RawStatementModel":
        return RawStatementModel(**RawStatementModel._kwargs_from_dto(dto))

    def to_dto(self) -> RawStatementDTO:
        return RawStatementDTO(**self._dto_kwargs())
