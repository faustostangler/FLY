from sqlalchemy import text

from domain.dto.statement_raw_dto import StatementRawDTO
from infrastructure.models.base_model import BaseModel
from infrastructure.repositories.raw_statement_repository import (
    SqlAlchemyStatementRawRepository,
)
from tests.conftest import DummyConfig, DummyLogger


def test_save_all_upserts(SessionLocal, engine):
    cfg = DummyConfig()
    repo = SqlAlchemyStatementRawRepository(
        connection_string=cfg.database.connection_string,
        config=cfg,
        logger=DummyLogger(),
    )
    repo.engine = engine
    repo.Session = SessionLocal
    BaseModel.metadata.drop_all(engine)
    BaseModel.metadata.create_all(engine)

    base = {
        "nsd": 1,
        "company_name": "ACME",
        "quarter": "2020-03-31",
        "version": "1",
        "grupo": "G",
        "quadro": "Q",
        "account": "01",
        "description": "d",
        "value": 1.0,
    }
    repo.save_all([StatementRawDTO.from_dict(base)])

    updated = base | {"value": 2.0}
    repo.save_all([StatementRawDTO.from_dict(updated)])

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM tbl_statements_raw")).scalar()
        value = conn.execute(
            text(
                """
                SELECT value FROM tbl_statements_raw
                WHERE nsd=1 AND account='01'
                """
            )
        ).scalar()

    assert count == 1
    assert value == 2.0
