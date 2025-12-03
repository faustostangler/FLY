from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from domain.dto.nsd_dto import NsdDTO

from .base_model import BaseModel


class NSDModel(BaseModel):
    """ORM model for the tbl_nsd table."""

    __tablename__ = "tbl_nsd"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nsd: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    company_name: Mapped[str] = mapped_column(
        String,
        ForeignKey("tbl_company.company_name"),
        nullable=False,
    )
    quarter: Mapped[Optional[datetime]] = mapped_column(DateTime)
    version: Mapped[Optional[str]] = mapped_column()
    nsd_type: Mapped[Optional[str]] = mapped_column()
    dri: Mapped[Optional[str]] = mapped_column()
    auditor: Mapped[Optional[str]] = mapped_column()
    responsible_auditor: Mapped[Optional[str]] = mapped_column()
    protocol: Mapped[Optional[str]] = mapped_column()
    sent_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reason: Mapped[Optional[str]] = mapped_column()

    __table_args__ = (Index("ix_nsd_company_name", "company_name"),)

    @staticmethod
    def from_dto(dto: NsdDTO) -> "NSDModel":
        """Converts a NsdDTO into an NSDModel for persistence."""
        return NSDModel(
            id=dto.id,
            nsd=dto.nsd,
            company_name=dto.company_name,
            quarter=dto.quarter,
            version=dto.version,
            nsd_type=dto.nsd_type,
            dri=dto.dri,
            auditor=dto.auditor,
            responsible_auditor=dto.responsible_auditor,
            protocol=dto.protocol,
            sent_date=dto.sent_date,
            reason=dto.reason,
        )

    def to_dto(self) -> NsdDTO:
        """Converts this ORM model back into a NsdDTO."""
        return NsdDTO(
            id=self.id,
            nsd=self.nsd,
            company_name=self.company_name,
            quarter=self.quarter,
            version=self.version,
            nsd_type=self.nsd_type,
            dri=self.dri,
            auditor=self.auditor,
            responsible_auditor=self.responsible_auditor,
            protocol=self.protocol,
            sent_date=self.sent_date,
            reason=self.reason,
        )
