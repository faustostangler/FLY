"""SQLAlchemy model for the valid companies read projection."""

from __future__ import annotations

from sqlalchemy import Column, Index, Integer, JSON, String

from domain.dtos.valid_company_read_model_dto import ValidCompanyReadModelDTO
from .base_model import BaseModel


class ValidCompanyReadModel(BaseModel):
    """ORM mapping for the ``read_valid_companies`` table."""

    __tablename__ = "read_valid_companies"

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
        Index("ix_read_valid_companies_company_name", "company_name"),
        Index("ix_read_valid_companies_cvm_code", "cvm_code"),
        Index("ix_read_valid_companies_segment", "company_segment"),
    )

    @classmethod
    def from_dto(cls, dto: ValidCompanyReadModelDTO) -> "ValidCompanyReadModel":
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

    def to_dto(self) -> ValidCompanyReadModelDTO:
        tickers = tuple(self.ticker_codes or [])
        return ValidCompanyReadModelDTO(
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
