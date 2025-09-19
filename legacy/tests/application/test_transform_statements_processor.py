from unittest.mock import MagicMock

from application.processors.transform_statements_processor import (
    TransformStatementsProcessor,
)
from domain.dtos.parsed_statement_dto import ParsedStatementDTO
from domain.ports import ParsedStatementRepositoryPort
from tests.conftest import DummyConfig, DummyLogger


def test_transform_processes_groups(monkeypatch):
    parsed_repo = MagicMock(spec=ParsedStatementRepositoryPort)

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
        parsed_repo=parsed_repo,
    )

    groups = [[MagicMock(spec=ParsedStatementDTO)]]
    usecase_inst.execute.return_value = [MagicMock(spec=ParsedStatementDTO)]

    result = processor.run(groups)

    usecase_inst.execute.assert_called_once_with(groups[0])
    parsed_repo.save_all.assert_called_once_with(usecase_inst.execute.return_value)
    assert result == [usecase_inst.execute.return_value]


def test_transform_returns_empty_when_no_groups(monkeypatch):
    parsed_repo = MagicMock(spec=ParsedStatementRepositoryPort)

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
        parsed_repo=parsed_repo,
    )

    result = processor.run([])
    assert result == []
    parsed_repo.save_all.assert_not_called()
