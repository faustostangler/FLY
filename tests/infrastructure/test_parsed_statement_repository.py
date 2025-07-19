from sqlalchemy import text

from domain.dto.parsed_statement_dto import ParsedStatementDTO
from infrastructure.models.base_model import Base
from infrastructure.repositories.parsed_statement_repository import (
    SqlAlchemyParsedStatementRepository,
)
from tests.conftest import DummyConfig, DummyLogger


def test_replace_and_exists(SessionLocal, engine):
    repo = SqlAlchemyParsedStatementRepository(
        config=DummyConfig(), logger=DummyLogger()
    )
    repo.engine = engine
    repo.Session = SessionLocal
    Base.metadata.create_all(engine)

    dto = ParsedStatementDTO(
        nsd="1",
        company_name="ACME",
        quarter="2020-03-31",
        version="1",
        grupo="G",
        quadro="Q",
        account="01",
        description="d",
        value=1.0,
        processing_hash="old",
    )
    repo.save_all([dto])

    new_dto = ParsedStatementDTO(
        nsd="2",
        company_name="ACME",
        quarter="2020-06-30",
        version="1",
        grupo="G",
        quadro="Q",
        account="02",
        description="d",
        value=2.0,
        processing_hash="new",
    )

    repo.replace_all_for_company("ACME", [new_dto], "hash123")

    assert repo.exists_with_hash("ACME", "hash123") is True

    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM tbl_parsed_statements")
        ).scalar()
        phash = conn.execute(
            text("SELECT processing_hash FROM tbl_parsed_statements")
        ).scalar()

    assert count == 1
    assert phash == "hash123"
