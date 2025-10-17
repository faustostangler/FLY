from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dtos.statement_ratio_dto import StatementRatioDTO
from infrastructure.models.statements_base_model import BaseStatementModel
from infrastructure.models.base_model import BaseModel, _YMDDate


class StatementRatioModel(BaseModel):
    """ORM model for ratio statement rows."""

    __tablename__ = "tbl_statements_ratio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nsd: Mapped[str] = mapped_column(
        String,
        ForeignKey("tbl_nsd.nsd"),
    )
    company_name: Mapped[str] = mapped_column(
        String,
        ForeignKey("tbl_company.company_name"),
    )
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[object] = mapped_column(_YMDDate, nullable=False)
    grupo: Mapped[str] = mapped_column(String, nullable=False)
    quadro: Mapped[str] = mapped_column(String, nullable=False)
    account: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "nsd",
            "company_name",
            "ticker",
            "date",
            "grupo",
            "quadro",
            "account",
            "version",
            name="uq_statements_ratio_fullkey",
        ),
        Index("ix_statements_ratio_company_name", "company_name"),
        Index("ix_statements_ratio_date", "date"),
        Index("ix_statements_ratio_account", "account"),
        Index("ix_statements_ratio_nsd", "nsd"),
        Index("ix_statements_ratio_company_name_date", "company_name", "date"),
    )

    _FIELDS = (
        "nsd",
        "company_name",
        "ticker",
        "date",
        "grupo",
        "quadro",
        "account",
        "description",
        "value",
        "version",
    )

    @classmethod
    def _kwargs_from_dto(cls, dto: object) -> dict:
        data = {field: getattr(dto, field) for field in cls._FIELDS}
        data["id"] = getattr(dto, "id", None)
        return data

    def _dto_kwargs(self) -> dict:
        data = {field: getattr(self, field) for field in self._FIELDS}
        data["id"] = self.id
        return data

    @staticmethod
    def from_dto(dto: StatementRatioDTO) -> "StatementRatioModel":
        return StatementRatioModel(**StatementRatioModel._kwargs_from_dto(dto))

    def to_dto(self) -> StatementRatioDTO:
        return StatementRatioDTO(**self._dto_kwargs())
