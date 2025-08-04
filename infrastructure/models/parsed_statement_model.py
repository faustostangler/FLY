from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dto.parsed_statement_dto import ParsedStatementDTO

from .abstract_statement_model import AbstractStatementModel


class ParsedStatementModel(AbstractStatementModel):
    """ORM model for parsed statement rows."""

    __tablename__ = "tbl_parsed_statements"

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
            name="uq_parsed_statements_fullkey",
        ),
        Index("ix_parsed_statements_cvm_code", "cvm_code"),
        Index("ix_parsed_statements_quarter", "quarter"),
        Index("ix_parsed_statements_account", "account"),
        Index("ix_parsed_statements_nsd", "nsd"),
        Index("ix_parsed_statements_cvm_code_quarter", "cvm_code", "quarter"),
    )

    processing_hash: Mapped[str | None] = mapped_column(String, index=True)

    _FIELDS = AbstractStatementModel._FIELDS + ("processing_hash",)

    @staticmethod
    def from_dto(dto: ParsedStatementDTO) -> "ParsedStatementModel":
        return ParsedStatementModel(**ParsedStatementModel._kwargs_from_dto(dto))

    def to_dto(self) -> ParsedStatementDTO:
        return ParsedStatementDTO(**self._dto_kwargs())
