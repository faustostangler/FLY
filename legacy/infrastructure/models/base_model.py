from sqlalchemy.orm import DeclarativeBase


class ORMBaseModel(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# # Alias used in tests and other modules
# Base = ORMBaseModel
