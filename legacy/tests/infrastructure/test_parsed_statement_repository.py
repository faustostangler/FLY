from dataclasses import replace

from sqlalchemy import text

from domain.dto.statement_fetched_dto import StatementFetchedDTO
from infrastructure.models.base_model import BaseModel
from infrastructure.repositories.fetched_statement_repository import (
    SqlAlchemyStatementFetchedRepository,
)
from tests.conftest import DummyConfig, DummyLogger


def test_replace_and_exists(SessionLocal, engine):
    cfg = DummyConfig()
    repo = SqlAlchemyStatementFetchedRepository(
        connection_string=cfg.database.connection_string,
        config=cfg,
        logger=DummyLogger(),
    )
    repo.engine = engine
    repo.Session = SessionLocal
    BaseModel.metadata.create_all(engine)

    dto = StatementFetchedDTO(
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

    new_dto = StatementFetchedDTO(
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
            text("SELECT COUNT(*) FROM tbl_statements_fetched")
        ).scalar()
        phash = conn.execute(
            text("SELECT processing_hash FROM tbl_statements_fetched")
        ).scalar()

    assert count == 1
    assert phash == "hash123"


def test_save_all_upserts(SessionLocal, engine):
    cfg = DummyConfig()
    repo = SqlAlchemyStatementFetchedRepository(
        connection_string=cfg.database.connection_string,
        config=cfg,
        logger=DummyLogger(),
    )
    repo.engine = engine
    repo.Session = SessionLocal
    BaseModel.metadata.drop_all(engine)
    BaseModel.metadata.create_all(engine)

    base = StatementFetchedDTO(
        nsd="1",
        company_name="ACME",
        quarter="2020-03-31",
        version="1",
        grupo="G",
        quadro="Q",
        account="01",
        description="d",
        value=1.0,
    )
    repo.save_all([base])

    updated = replace(base, value=2.0)
    repo.save_all([updated])

    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM tbl_statements_fetched")
        ).scalar()
        value = conn.execute(
            text(
                """
                SELECT value FROM tbl_statements_fetched
                WHERE nsd='1' AND account='01'
                """
            )
        ).scalar()

    assert count == 1
    assert value == 2.0
