from sqlalchemy import text

from domain.dto.company_data_dto import CompanyDataDTO
from infrastructure.models.base_model import BaseModel
from infrastructure.repositories.repository_company import (
    SqlAlchemyRepositoryCompanyData,
)
from tests.conftest import DummyConfig, DummyLogger


def test_save_all(SessionLocal, engine):
    cfg = DummyConfig()
    repo = SqlAlchemyRepositoryCompanyData(
        connection_string=cfg.database.connection_string,
        config=cfg,
        logger=DummyLogger(),
    )
    # use shared engine
    repo.engine = engine
    repo.Session = SessionLocal
    BaseModel.metadata.create_all(engine)

    companies = [
        CompanyDataDTO.from_dict({"issuing_company": "AAA", "company_name": "Alpha"}),
        CompanyDataDTO.from_dict({"issuing_company": "BBB", "company_name": "Beta"}),
    ]
    repo.save_all(companies)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM tbl_company")).scalar()
    assert result == 2


def test_save_all_json_string(SessionLocal, engine):
    cfg = DummyConfig()
    repo = SqlAlchemyRepositoryCompanyData(
        connection_string=cfg.database.connection_string,
        config=cfg,
        logger=DummyLogger(),
    )
    repo.engine = engine
    repo.Session = SessionLocal
    BaseModel.metadata.drop_all(engine)
    BaseModel.metadata.create_all(engine)

    json_codes = '[{"code": "AAA", "isin": "123"}]'
    companies = [
        CompanyDataDTO.from_dict(
            {
                "issuing_company": "AAA",
                "company_name": "Alpha",
                "other_codes": json_codes,
            }
        )
    ]

    repo.save_all(companies)

    with engine.connect() as conn:
        saved = conn.execute(text("SELECT other_codes FROM tbl_company")).scalar()

    assert saved == json_codes


def test_save_all_upserts(SessionLocal, engine):
    cfg = DummyConfig()
    repo = SqlAlchemyRepositoryCompanyData(
        connection_string=cfg.database.connection_string,
        config=cfg,
        logger=DummyLogger(),
    )
    repo.engine = engine
    repo.Session = SessionLocal
    BaseModel.metadata.drop_all(engine)
    BaseModel.metadata.create_all(engine)

    first = [
        CompanyDataDTO.from_dict(
            {"issuing_company": "AAA", "company_name": "Alpha", "cnpj": "1"}
        )
    ]
    repo.save_all(first)

    second = [
        CompanyDataDTO.from_dict(
            {"issuing_company": "AAA", "company_name": "Alpha", "cnpj": "2"}
        )
    ]
    repo.save_all(second)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM tbl_company")).scalar()
        cnpj = conn.execute(
            text("SELECT cnpj FROM tbl_company WHERE cvm_code='AAA'")
        ).scalar()

    assert result == 1
    assert cnpj == "2"
