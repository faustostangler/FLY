from unittest.mock import MagicMock

from application.processors.fetch_statements_processor import (
    FetchStatementsProcessor,
)
from application.processors.parse_statements_processor import (
    ParseStatementsProcessor,
)
from application.processors.transform_statements_processor import (
    TransformStatementsProcessor,
)
from domain.dto import NsdDTO
from domain.dto.statement_fetched_dto import StatementFetchedDTO
from domain.dto.statement_raw_dto import StatementRawDTO
from tests.conftest import DummyLogger


class DummyConfig:
    class Domain:
        statements_types = ("dre",)

    class Global:
        max_workers = 1
        queue_size = 10
        threshold = 10

    class Transformers:
        math_target_accounts = ("01",)
        math_year_end_prefixes = ()
        math_cumulative_prefixes = ()

    domain = Domain()
    global_settings = Global()
    transformers = Transformers()


def test_full_statement_pipeline(monkeypatch):
    config = DummyConfig()
    logger = DummyLogger()

    company_repo = MagicMock()
    nsd_repo = MagicMock()
    raw_repo = MagicMock()
    fetched_repo = MagicMock()
    source = MagicMock()
    collector = MagicMock()
    worker_pool = MagicMock()

    fetch_processor = FetchStatementsProcessor(
        logger=logger,
        config=config,
        source=source,
        company_repo=company_repo,
        nsd_repo=nsd_repo,
        raw_statement_repo=raw_repo,
        fetched_statements_repo=fetched_repo,
        metrics_collector=collector,
        worker_pool_executor=worker_pool,
    )

    nsd = NsdDTO(
        nsd="1",
        company_name="Comp",
        quarter=None,
        version=None,
        nsd_type=None,
        dri=None,
        auditor=None,
        responsible_auditor=None,
        protocol=None,
        sent_date=None,
        reason=None,
    )
    raw_row = StatementRawDTO(
        nsd="1",
        company_name="Comp",
        quarter=None,
        version=None,
        grupo="G",
        quadro="Q",
        account="acc",
        description="desc",
        value=1.0,
    )
    monkeypatch.setattr(fetch_processor, "_build_targets", lambda: [nsd])
    fetch_processor.fetch_usecase.fetch_statement_rows = MagicMock(
        return_value=[(nsd, [raw_row])]
    )

    raw_rows = fetch_processor.run()

    parse_processor = ParseStatementsProcessor(
        logger=logger,
        repository=fetched_repo,
        config=config,
        worker_pool_executor=worker_pool,
        metrics_collector=collector,
    )
    fetched_dto = StatementFetchedDTO(
        nsd="1",
        company_name="Comp",
        quarter=None,
        version=None,
        grupo="G",
        quadro="Q",
        account="acc",
        description="desc",
        value=1.0,
        processing_hash="hash",
    )
    parse_processor.parse_usecase.parse_and_store_row = MagicMock(
        return_value=fetched_dto
    )
    worker_pool.run = MagicMock(return_value=MagicMock(items=[[fetched_dto]]))
    monkeypatch.setattr(parse_processor.parse_usecase, "finalize", lambda: None)

    fetched_groups = parse_processor.run(raw_rows)

    monkeypatch.setattr(
        "application.processors.transform_statements_processor.MathStatementTransformerAdapter",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        "application.processors.transform_statements_processor.IntelStatementTransformerAdapter",
        MagicMock(return_value=MagicMock()),
    )
    transform_processor = TransformStatementsProcessor(
        config=config, logger=logger, fetched_repo=fetched_repo
    )
    transform_processor.transform_usecase.execute = MagicMock(side_effect=lambda g: g)
    result = transform_processor.run(fetched_groups)

    assert result == [[fetched_dto]]
