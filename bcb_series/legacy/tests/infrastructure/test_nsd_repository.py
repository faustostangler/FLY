from sqlalchemy import text

from domain.dto.nsd_dto import NsdDTO
from infrastructure.models.base_model import BaseModel
from infrastructure.repositories.repository_nsd import SqlAlchemyNsdRepository
from tests.conftest import DummyConfig, DummyLogger


def test_save_all_upserts(SessionLocal, engine):
    cfg = DummyConfig()
    repo = SqlAlchemyNsdRepository(
        connection_string=cfg.database.connection_string,
        config=cfg,
        logger=DummyLogger(),
    )
    repo.engine = engine
    repo.Session = SessionLocal
    BaseModel.metadata.drop_all(engine)
    BaseModel.metadata.create_all(engine)

    first = [NsdDTO.from_dict({"nsd": 1, "company_name": "ACME"})]
    repo.save_all(first)

    second = [NsdDTO.from_dict({"nsd": 1, "company_name": "ACME", "reason": "dup"})]
    repo.save_all(second)

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM tbl_nsd")).scalar()
        reason = conn.execute(text("SELECT reason FROM tbl_nsd WHERE nsd=1")).scalar()

    assert count == 1
    assert reason == "dup"
