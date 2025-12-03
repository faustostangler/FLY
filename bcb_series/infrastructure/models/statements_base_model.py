from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.models.base_model import (
    BaseModel,
    _YMDDate,  # mesmo formato de data
)


class BaseStatementModel(BaseModel):
    """Base ORM model for raw and fetched statement rows."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nsd: Mapped[str] = mapped_column()
    quarter: Mapped[datetime | None] = mapped_column(_YMDDate)   # antes: str | None
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
        data = {field: getattr(dto, field) for field in cls._FIELDS}
        data["id"] = getattr(dto, "id", None)
        return data

    def _dto_kwargs(self) -> dict:
        data = {field: getattr(self, field) for field in self._FIELDS}
        data["id"] = self.id
        return data

