"""SQLAlchemy model for the eligible companies read projection."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, Index, Integer, String

from domain.dtos.company_data_dto import CodeDTO
from domain.dtos.company_eligible_dto import CompanyEligibleDTO

from infrastructure.models.base_model import BaseModel, _YMDDate


class CompanyEligibleModel(BaseModel):
    """ORM mapping for the ``tbl_company_eligible`` table."""

    __tablename__ = "tbl_company_eligible"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cvm_code = Column(String, nullable=True)
    issuing_company = Column(String, nullable=True)
    trading_name = Column(String, nullable=True)
    company_name = Column(String, nullable=False, unique=True)
    cnpj = Column(String, nullable=True)

    ticker_codes = Column(JSON, nullable=False, default=list)
    isin_codes = Column(JSON, nullable=False, default=list)
    other_codes = Column(JSON, nullable=False, default=list)
    market = Column(String, nullable=True)

    industry_sector = Column(String, nullable=True)
    industry_subsector = Column(String, nullable=True)
    industry_segment = Column(String, nullable=True)
    industry_classification = Column(String, nullable=True)
    industry_classification_eng = Column(String, nullable=True)
    activity = Column(String, nullable=True)

    company_segment = Column(String, nullable=True)
    company_segment_eng = Column(String, nullable=True)
    company_category = Column(String, nullable=True)
    company_type = Column(String, nullable=True)

    listing_segment = Column(String, nullable=True)
    registrar = Column(String, nullable=True)
    website = Column(String, nullable=True)
    institution_common = Column(String, nullable=True)
    institution_preferred = Column(String, nullable=True)

    status = Column(String, nullable=True)
    market_indicator = Column(String, nullable=True)
    code = Column(String, nullable=True)
    has_bdr = Column(Boolean, nullable=True)
    type_bdr = Column(String, nullable=True)
    has_quotation = Column(Boolean, nullable=True)
    has_emissions = Column(Boolean, nullable=True)

    date_quotation = Column(_YMDDate, nullable=True)
    last_date = Column(_YMDDate, nullable=True)
    listing_date = Column(_YMDDate, nullable=True)

    reason = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_tbl_company_eligible_company_name", "company_name"),
        Index("ix_tbl_company_eligible_cvm_code", "cvm_code"),
        Index("ix_tbl_company_eligible_segment", "company_segment"),
    )

    @staticmethod
    def _serialize_other_codes(other_codes: tuple[CodeDTO, ...]) -> list[dict[str, str | None]]:
        return [
            {"code": code.code, "isin": code.isin}
            for code in other_codes
        ]

    @staticmethod
    def _deserialize_other_codes(raw: list[dict[str, str | None]] | None) -> tuple[CodeDTO, ...]:
        if not raw:
            return tuple()
        return tuple(CodeDTO(code=item.get("code"), isin=item.get("isin")) for item in raw)

    @classmethod
    def from_dto(cls, dto: CompanyEligibleDTO) -> "CompanyEligibleModel":
        return cls(
            id=dto.id,
            company_name=dto.company_name,
            cvm_code=dto.cvm_code,
            issuing_company=dto.issuing_company,
            trading_name=dto.trading_name,
            cnpj=dto.cnpj,
            ticker_codes=list(dto.ticker_codes),
            isin_codes=list(dto.isin_codes),
            other_codes=cls._serialize_other_codes(dto.other_codes),
            market=dto.market,
            industry_sector=dto.industry_sector,
            industry_subsector=dto.industry_subsector,
            industry_segment=dto.industry_segment,
            industry_classification=dto.industry_classification,
            industry_classification_eng=dto.industry_classification_eng,
            activity=dto.activity,
            company_segment=dto.company_segment,
            company_segment_eng=dto.company_segment_eng,
            company_category=dto.company_category,
            company_type=dto.company_type,
            listing_segment=dto.listing_segment,
            registrar=dto.registrar,
            website=dto.website,
            institution_common=dto.institution_common,
            institution_preferred=dto.institution_preferred,
            status=dto.status,
            market_indicator=dto.market_indicator,
            code=dto.code,
            has_bdr=dto.has_bdr,
            type_bdr=dto.type_bdr,
            has_quotation=dto.has_quotation,
            has_emissions=dto.has_emissions,
            date_quotation=dto.date_quotation,
            last_date=dto.last_date,
            listing_date=dto.listing_date,
            reason=dto.reason,
        )

    def to_dto(self) -> CompanyEligibleDTO:
        return CompanyEligibleDTO(
            id=self.id,
            company_name=self.company_name,
            cvm_code=self.cvm_code,
            issuing_company=self.issuing_company,
            trading_name=self.trading_name,
            cnpj=self.cnpj,
            ticker_codes=tuple(self.ticker_codes or []),
            isin_codes=tuple(self.isin_codes or []),
            other_codes=self._deserialize_other_codes(self.other_codes),
            market=self.market,
            industry_sector=self.industry_sector,
            industry_subsector=self.industry_subsector,
            industry_segment=self.industry_segment,
            industry_classification=self.industry_classification,
            industry_classification_eng=self.industry_classification_eng,
            activity=self.activity,
            company_segment=self.company_segment,
            company_segment_eng=self.company_segment_eng,
            company_category=self.company_category,
            company_type=self.company_type,
            listing_segment=self.listing_segment,
            registrar=self.registrar,
            website=self.website,
            institution_common=self.institution_common,
            institution_preferred=self.institution_preferred,
            status=self.status,
            market_indicator=self.market_indicator,
            code=self.code,
            has_bdr=self.has_bdr,
            type_bdr=self.type_bdr,
            has_quotation=self.has_quotation,
            has_emissions=self.has_emissions,
            date_quotation=self.date_quotation,
            last_date=self.last_date,
            listing_date=self.listing_date,
            reason=self.reason,
        )
