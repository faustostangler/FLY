from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import String, TypeDecorator


class BaseModel(DeclarativeBase):
    """Abstract base class for all SQLAlchemy ORM models.

    Inherit from this class to define database tables.
    It ensures that all models share the same SQLAlchemy declarative base.
    """

    # No additional logic needed; serves as the base for ORM models
    pass

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



