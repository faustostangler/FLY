from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base_model import BaseModel


class AbstractStatementModel(BaseModel):
    """Base ORM model for raw and parsed statement rows."""

    __abstract__ = True
    __table_args__ = (
        UniqueConstraint(
            "nsd",
            "company_name",
            "quarter",
            "version",
            "grupo",
            "quadro",
            "account",
            name="uq_statements_temp",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nsd: Mapped[str] = mapped_column(String, ForeignKey("tbl_nsd.nsd"))
    company_name: Mapped[str | None] = mapped_column(
        ForeignKey("tbl_company.company_name")
    )
    quarter: Mapped[str | None] = mapped_column()
    version: Mapped[str | None] = mapped_column()
    grupo: Mapped[str] = mapped_column()
    quadro: Mapped[str] = mapped_column()
    account: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    value: Mapped[float] = mapped_column()

    _FIELDS = (
        "nsd",
        "company_name",
        "quarter",
        "version",
        "grupo",
        "quadro",
        "account",
        "description",
        "value",
    )

    @classmethod
    def _kwargs_from_dto(cls, dto: object) -> dict:
        return {field: getattr(dto, field) for field in cls._FIELDS}

    def _dto_kwargs(self) -> dict:
        data = {field: getattr(self, field) for field in self._FIELDS}
        data["id"] = self.id
        return data
