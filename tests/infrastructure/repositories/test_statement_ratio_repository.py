from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from domain.dtos.statement_ratio_dto import StatementRatioDTO
from infrastructure.repositories.repository_statements_ratio import (
    StatementRatioRepository,
)
from infrastructure.models import company_data_model  # noqa: F401
from infrastructure.models import nsd_model  # noqa: F401
from infrastructure.uow.uow import UowFactory


@pytest.fixture()
def config(tmp_path):
    db_path = tmp_path / "ratios.db"
    database = SimpleNamespace(
        db_filename=str(db_path),
        connection_string=f"sqlite:///{db_path}",
        tables={},
    )
    repository = SimpleNamespace(batch_size=50, persistence_threshold=1)
    return SimpleNamespace(database=database, repository=repository)


@pytest.fixture()
def logger():
    return MagicMock()


@pytest.fixture()
def repository(config, logger):
    return StatementRatioRepository(config=config, logger=logger)


@pytest.fixture()
def uow_factory(repository):
    return UowFactory(session_factory=repository.Session)


def _make_ratio(value: float = 10.0) -> StatementRatioDTO:
    return StatementRatioDTO(
        nsd="123",
        company_name="Example SA",
        date=datetime(2024, 1, 31),
        version="1",
        grupo="G",
        quadro="Q",
        account="ACC",
        description="Ratio",
        value=value,
    )


def test_save_all_persists_with_uow_control(repository, uow_factory):
    dto = _make_ratio(25.0)

    with uow_factory() as uow:
        repository.save_all([dto], uow=uow)
        assert uow.session.in_transaction()
        persisted = repository.get_by_company_name(dto.company_name, uow=uow)
        assert len(persisted) == 1
        assert persisted[0].value == pytest.approx(25.0)
        uow.commit()

    with uow_factory() as uow:
        rows = repository.get_by_company_name(dto.company_name, uow=uow)
        assert len(rows) == 1
        assert rows[0].value == pytest.approx(25.0)


def test_save_all_upserts_on_conflict(repository, uow_factory):
    original = _make_ratio(10.0)
    updated = replace(original, value=42.0)

    with uow_factory() as uow:
        repository.save_all([original], uow=uow)
        uow.commit()

    with uow_factory() as uow:
        repository.save_all([updated], uow=uow)
        uow.commit()

    with uow_factory() as uow:
        rows = repository.get_by_company_name(original.company_name, uow=uow)
        assert len(rows) == 1
        assert rows[0].value == pytest.approx(42.0)


def test_nested_batches_and_none_are_ignored(repository, uow_factory):
    dto = _make_ratio(17.5)

    with uow_factory() as uow:
        repository.save_all([[dto, None]], uow=uow)
        uow.commit()

    with uow_factory() as uow:
        rows = repository.get_by_company_name(dto.company_name, uow=uow)
        assert len(rows) == 1
        assert rows[0].value == pytest.approx(17.5)


def test_rollback_discards_uncommitted_changes(repository, uow_factory):
    dto = _make_ratio(33.3)

    with uow_factory() as uow:
        repository.save_all([dto], uow=uow)
        uow.rollback()

    with uow_factory() as uow:
        rows = repository.get_by_company_name(dto.company_name, uow=uow)
        assert rows == []
