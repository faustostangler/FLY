from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    """Abstract base class for all SQLAlchemy ORM models.

    Inherit from this class to define database tables.
    It ensures that all models share the same SQLAlchemy declarative base.
    """

    # No additional logic needed; serves as the base for ORM models
    pass
