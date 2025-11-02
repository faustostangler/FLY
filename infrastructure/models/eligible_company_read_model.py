"""SQLAlchemy model for the eligible companies read projection."""

from __future__ import annotations

from sqlalchemy import JSON, Column, Index, Integer, String

from domain.dtos.eligible_company_read_model_dto import EligibleCompanyReadModelDTO

from .base_model import BaseModel


class EligibleCompanyReadModel(BaseModel):
    """ORM mapping for the ``proj_eligible_companies`` table."""

    __tablename__ = "proj_eligible_companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, nullable=False, unique=True)
    cvm_code = Column(String, nullable=True)
    trading_name = Column(String, nullable=True)
    industry_sector = Column(String, nullable=True)
    industry_subsector = Column(String, nullable=True)
    industry_segment = Column(String, nullable=True)
    company_segment = Column(String, nullable=True)
    ticker_codes = Column(JSON, nullable=False, default=list)
    reason = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_proj_eligible_companies_company_name", "company_name"),
        Index("ix_proj_eligible_companies_cvm_code", "cvm_code"),
        Index("ix_proj_eligible_companies_segment", "company_segment"),
    )

    @classmethod
    def from_dto(cls, dto: EligibleCompanyReadModelDTO) -> "EligibleCompanyReadModel":
        return cls(
            company_name=dto.company_name,
            cvm_code=dto.cvm_code,
            trading_name=dto.trading_name,
            industry_sector=dto.industry_sector,
            industry_subsector=dto.industry_subsector,
            industry_segment=dto.industry_segment,
            company_segment=dto.company_segment,
            ticker_codes=list(dto.ticker_codes),
            reason=dto.reason,
        )

    def to_dto(self) -> EligibleCompanyReadModelDTO:
        tickers = tuple(self.ticker_codes or [])
        return EligibleCompanyReadModelDTO(
            company_name=self.company_name,
            cvm_code=self.cvm_code,
            trading_name=self.trading_name,
            industry_sector=self.industry_sector,
            industry_subsector=self.industry_subsector,
            industry_segment=self.industry_segment,
            company_segment=self.company_segment,
            ticker_codes=tickers,
            reason=self.reason,
        )
