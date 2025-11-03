"""Metadata table tracking eligible companies projection versions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from infrastructure.models.base_model import BaseModel


class CompanyEligibleProjectionModel(BaseModel):
    """Persist metadata for each eligible companies projection calculation."""

    __tablename__ = "tbl_company_eligible_projection"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String, nullable=False, unique=True)
    evaluated_count = Column(Integer, nullable=False)
    eligible_count = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_current = Column(Boolean, nullable=False, default=False, index=True)

    __table_args__ = (
        UniqueConstraint("version", name="uq_company_eligible_projection_version"),
    )
