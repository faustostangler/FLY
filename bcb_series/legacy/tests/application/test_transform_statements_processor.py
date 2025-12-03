from unittest.mock import MagicMock

from application.processors.transform_statements_processor import (
    TransformStatementsProcessor,
)
from domain.dto.statement_fetched_dto import StatementFetchedDTO
from domain.ports import RepositoryStatementFetchedPort
from tests.conftest import DummyConfig, DummyLogger


def test_transform_processes_groups(monkeypatch):
    fetched_repo = MagicMock(spec=RepositoryStatementFetchedPort)

    monkeypatch.setattr(
        "application.processors.transform_statements_processor.MathStatementTransformerAdapter",
        MagicMock(),
    )
    monkeypatch.setattr(
        "application.processors.transform_statements_processor.IntelStatementTransformerAdapter",
        MagicMock(),
    )

    usecase_cls = MagicMock()
    usecase_inst = MagicMock()
    usecase_cls.return_value = usecase_inst
    monkeypatch.setattr(
        "application.processors.transform_statements_processor.TransformStatementsUseCase",
        usecase_cls,
    )

    processor = TransformStatementsProcessor(
        logger=DummyLogger(),
        config=DummyConfig(),
        fetched_repo=fetched_repo,
    )

    groups = [[MagicMock(spec=StatementFetchedDTO)]]
    usecase_inst.execute.return_value = [MagicMock(spec=StatementFetchedDTO)]

    result = processor.run(groups)

    usecase_inst.execute.assert_called_once_with(groups[0])
    fetched_repo.save_all.assert_called_once_with(usecase_inst.execute.return_value)
    assert result == [usecase_inst.execute.return_value]


def test_transform_returns_empty_when_no_groups(monkeypatch):
    fetched_repo = MagicMock(spec=RepositoryStatementFetchedPort)

    monkeypatch.setattr(
        "application.processors.transform_statements_processor.MathStatementTransformerAdapter",
        MagicMock(),
    )
    monkeypatch.setattr(
        "application.processors.transform_statements_processor.IntelStatementTransformerAdapter",
        MagicMock(),
    )

    processor = TransformStatementsProcessor(
        logger=DummyLogger(),
        config=DummyConfig(),
        fetched_repo=fetched_repo,
    )

    result = processor.run([])
    assert result == []
    fetched_repo.save_all.assert_not_called()
