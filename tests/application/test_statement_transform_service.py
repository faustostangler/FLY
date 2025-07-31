from unittest.mock import MagicMock

from application.services.statement_transform_service import StatementTransformService
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import (
    SqlAlchemyParsedStatementRepositoryPort,
    SqlAlchemyRawStatementRepositoryPort,
)
from tests.conftest import DummyConfig, DummyLogger


def test_transform_all_processes_new_data(monkeypatch):
    raw_repo = MagicMock(spec=SqlAlchemyRawStatementRepositoryPort)
    parsed_repo = MagicMock(spec=SqlAlchemyParsedStatementRepositoryPort)

    raw_repo.get_existing_by_columns.return_value = [("ACME",)]
    rows = [MagicMock(spec=RawStatementDTO)]
    raw_repo.get_by_company_name.return_value = rows

    monkeypatch.setattr(
        "application.services.statement_transform_service.compute_hash",
        lambda _: "hash1",
    )

    monkeypatch.setattr(
        "application.services.statement_transform_service.MathStatementTransformerAdapter",
        MagicMock(),
    )
    monkeypatch.setattr(
        "application.services.statement_transform_service.IntelStatementTransformerAdapter",
        MagicMock(),
    )

    usecase_cls = MagicMock()
    usecase_inst = MagicMock()
    usecase_cls.return_value = usecase_inst
    monkeypatch.setattr(
        "application.services.statement_transform_service.TransformStatementsUseCase",
        usecase_cls,
    )

    parsed_repo.exists_with_hash.return_value = False

    service = StatementTransformService(
        logger=DummyLogger(),
        raw_repo=raw_repo,
        parsed_repo=parsed_repo,
        config=DummyConfig(),
    )

    service.transform_all()

    raw_repo.get_existing_by_columns.assert_called_once_with("company_name")
    raw_repo.get_by_company_name.assert_called_once_with("ACME")
    usecase_inst.execute.assert_called_once_with(rows)
    parsed_repo.replace_all_for_company.assert_called_once_with(
        "ACME", usecase_inst.execute.return_value, "hash1"
    )


def test_transform_all_skips_when_no_changes(monkeypatch):
    raw_repo = MagicMock(spec=SqlAlchemyRawStatementRepositoryPort)
    parsed_repo = MagicMock(spec=SqlAlchemyParsedStatementRepositoryPort)

    raw_repo.get_existing_by_columns.return_value = [("ACME",)]
    rows = [MagicMock(spec=RawStatementDTO)]
    raw_repo.get_by_company_name.return_value = rows

    monkeypatch.setattr(
        "application.services.statement_transform_service.compute_hash",
        lambda _: "hash1",
    )

    monkeypatch.setattr(
        "application.services.statement_transform_service.MathStatementTransformerAdapter",
        MagicMock(),
    )
    monkeypatch.setattr(
        "application.services.statement_transform_service.IntelStatementTransformerAdapter",
        MagicMock(),
    )

    parsed_repo.exists_with_hash.return_value = True

    service = StatementTransformService(
        logger=DummyLogger(),
        raw_repo=raw_repo,
        parsed_repo=parsed_repo,
        config=DummyConfig(),
    )

    service.transform_all()

    parsed_repo.replace_all_for_company.assert_not_called()
