from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, String

from .base_model import BaseModel


class _YMDDate(TypeDecorator):
    """Persist as 'YYYY-MM-DD' (TEXT) e expõe como datetime no Python."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        # se vier string, corta no dia e confia no formato já limpo
        return str(value)[:10]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # garante parse sempre do Y-M-D
        return datetime.strptime(str(value)[:10], "%Y-%m-%d")




class BaseStatementModel(BaseModel):
    """Base ORM model for raw and fetched statement rows."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nsd: Mapped[str] = mapped_column()
    quarter: Mapped[datetime | None] = mapped_column(_YMDDate)
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
