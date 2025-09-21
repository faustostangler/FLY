from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping, Sequence, cast
from unittest.mock import MagicMock

import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# <<<<<<< codex/fix-unrealistic-time-progression-logs-0j1j18
from application.processors.nsd_processor import NsdProcessor, _NsdTxnAggregator
# =======
# import application.processors.nsd_processor as nsd_module
# from application.processors.nsd_processor import NsdProcessor, _StageTimeline
# >>>>>>> 2025-09-09-Fetch-Adjustments
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO


def _build_processor() -> tuple[NsdProcessor, MagicMock]:
    config = SimpleNamespace(
        paths=SimpleNamespace(
            temp_dir=Path("/tmp"),
            log_dir=Path("/tmp"),
            data_dir=Path("/tmp"),
            root_dir=Path("/tmp"),
        ),
        fly_settings=SimpleNamespace(app_name="TestApp", version="0", show_path=False),
        database=SimpleNamespace(
            db_filename=":memory:",
            connection_string="sqlite://",
            tables={},
        ),
        logging=SimpleNamespace(
            log_dir=Path("/tmp"),
            log_file_name="test.log",
            level="INFO",
            show_path=False,
        ),
        scraping=SimpleNamespace(
            user_agents=[],
            referers=[],
            languages=[],
            test_internet="",
            timeout=1,
            max_attempts=1,
            linear_holes=1,
        ),
        domain=SimpleNamespace(
            words_to_remove=tuple(),
            statements_types=tuple(),
            base_currency="BRL",
            nsd_gap_days=0,
            recency_year=0,
        ),
        repository=SimpleNamespace(batch_size=1, persistence_threshold=1),
        exchange=SimpleNamespace(
            language="pt-BR",
            company_data_endpoint={},
            nsd_endpoint="",
        ),
        worker_pool=SimpleNamespace(max_workers=1, queue_size=1),
        statements=SimpleNamespace(
            statement_items=tuple(),
            nsd_type_map={},
            capital_items=[],
            url_df="",
            url_capital="",
        ),
    )
    logger_mock: MagicMock = MagicMock(spec=LoggerPort)

    processor = NsdProcessor(
        config=cast(ConfigPort, config),
        logger=cast(LoggerPort, logger_mock),
        nsd_repository=MagicMock(),
        company_repository=MagicMock(),
        statements_raw_repository=MagicMock(),
        statements_fetched_repository=MagicMock(),
        scraper_nsd=MagicMock(),
        scraper_statements_raw=MagicMock(),
        policy=MagicMock(),
        financial_normalizer=MagicMock(),
        ratios_calculator=MagicMock(),
        uow_factory=MagicMock(),
    )

    return processor, logger_mock


def _make_nsd() -> NsdDTO:
    return NsdDTO(
        nsd=123,
        company_name="Example SA",
        quarter=datetime(2020, 3, 31),
        version=1,
        nsd_type="FORM",
        dri=None,
        auditor=None,
        responsible_auditor=None,
        protocol=None,
        sent_date=datetime(2020, 4, 20, 10, 30),
        reason=None,
    )


def _make_raw() -> StatementRawDTO:
    return StatementRawDTO(
        nsd="123",
        company_name="Example SA",
        quarter=datetime(2020, 3, 31),
        version="1",
        grupo="G",
        quadro="Q",
        account="ACC",
        description="Description",
        value=10.0,
    )


def _make_fetched() -> StatementFetchedDTO:
    return StatementFetchedDTO(
        nsd="123",
        company_name="Example SA",
        quarter=datetime(2020, 3, 31),
        version="1",
        grupo="G",
        quadro="Q",
        account="ACC",
        description="Description",
        value=10.0,
    )


def test_resolve_progress_start_time_reuses_first_value() -> None:
    processor, _ = _build_processor()

    first = processor._resolve_progress_start_time(100.0)
    second = processor._resolve_progress_start_time(150.0)

    assert first == second == 100.0


def test_resolve_progress_start_time_resets_when_requested() -> None:
    processor, _ = _build_processor()

    processor._resolve_progress_start_time(50.0)
    updated = processor._resolve_progress_start_time(200.0, reset=True)

    assert updated == 200.0


def test_build_progress_payload_defaults_total_size_when_missing() -> None:
    processor, _ = _build_processor()
    task = WorkerTaskDTO(index=4, data="payload", worker_id="worker", total_size=None)

    payload = processor._build_progress_payload(task=task, start_time=123.456)

    assert payload["size"] == 5
    assert payload["index"] == 4
    assert payload["start_time"] == 123.456


def test_run_logs_missing_nsd_with_collector_metrics() -> None:
    processor, logger = _build_processor()
    logger.reset_mock()

    nsd_collector = SimpleNamespace(download_bytes=0, network_bytes=0)
    processor.scraper_nsd.metrics_collector = nsd_collector
    processor.scraper_statements_raw.metrics_collector = nsd_collector

    def _fetch_one(_: int) -> None:
        nsd_collector.download_bytes = 512
        nsd_collector.network_bytes = 512
        return None

    processor.scraper_nsd.fetch_one.side_effect = _fetch_one

    task = WorkerTaskDTO(index=0, data="123", worker_id="worker", total_size=1)

    processor.run(task)

    logger.log.assert_called_once()
    _, kwargs = logger.log.call_args
    assert kwargs["extra"] == {
        "Download": "512.00B",
        "Total download": "512.00B",
    }


# <<<<<<< codex/fix-unrealistic-time-progression-logs-0j1j18
def test_log_stage_uses_existing_progress_formatter_payload() -> None:
    processor, logger = _build_processor()
    logger.reset_mock()

    nsd = NsdDTO(
        nsd=123,
        company_name="Example SA",
        quarter=datetime(2010, 12, 31),
        version=1,
        nsd_type="FORM",
        dri=None,
        auditor=None,
        responsible_auditor=None,
        protocol=None,
        sent_date=datetime(2010, 4, 20, 9, 35, 15),
        reason=None,
    )

    progress = {"index": 0, "size": 10, "start_time": 42.0}

    processor._log_stage("NSD", nsd, progress=progress, worker_id="worker")

    logger.log.assert_called_once()
    _, kwargs = logger.log.call_args

    assert kwargs["progress"]["stage"] == "NSD"
    assert kwargs["progress"]["extra_info"] == [
        "2010-12-31 v1 | 2010-04-20 09:35:15 | FORM Example SA"
    ]
    assert kwargs["extra"] is None


def test_log_stage_forwards_extra_payload() -> None:
    processor, logger = _build_processor()
    logger.reset_mock()

    nsd = _make_nsd()
    progress = {"index": 0, "size": 1, "start_time": 42.0}
    extra_payload = {"Download": "1.00KB", "Total download": "2.00KB"}

    processor._log_stage(
        "NSD",
        nsd,
        progress=progress,
        worker_id="worker",
        extra=extra_payload,
    )

    logger.log.assert_called_once()
    _, kwargs = logger.log.call_args
    assert kwargs["extra"] == extra_payload
# =======
# def test_stage_timeline_summary_tracks_elapsed(monkeypatch) -> None:
#     timeline = _StageTimeline(started_at=0.0)
#     perf_counter_values = iter([0.5, 2.5])
#     monkeypatch.setattr(nsd_module.time, "perf_counter", lambda: next(perf_counter_values))

#     first = timeline.mark("NSD")
#     second = timeline.mark("RAW")

#     assert first == "pipeline: nsd=500ms"
#     assert second == "pipeline: nsd=500ms raw=0h00m02s"
# >>>>>>> 2025-09-09-Fetch-Adjustments


def test_aggregator_flush_without_nsd_skips_all_persistence() -> None:
    save_callback = MagicMock()
    raw_repo = MagicMock()
    fetched_repo = MagicMock()
    aggregator = _NsdTxnAggregator(
        save_callback=save_callback,
        statements_raw_repository=raw_repo,
        statements_fetched_repository=fetched_repo,
        chunk_size=10,
    )

    aggregator.add_raw_many([_make_raw()])
    aggregator.add_fetched_many([_make_fetched()])

    aggregator.flush(uow=MagicMock(), include_raw=True, include_fetched=True)

    save_callback.assert_not_called()
    raw_repo.save_all.assert_not_called()
    fetched_repo.save_all.assert_not_called()


def test_finalize_nsd_only_persists_nsd_when_not_statement() -> None:
    processor, _ = _build_processor()
    processor.company_repository.iter_existing_by_columns.return_value = []
    aggregator = processor._create_aggregator()
    aggregator.add_raw_many([_make_raw()])
    aggregator.add_fetched_many([_make_fetched()])
    uow = MagicMock()

    processor._finalize_nsd(nsd=_make_nsd(), aggregator=aggregator, uow=uow)

    processor.nsd_repository.save_all.assert_called_once()
    processor.statements_raw_repository.save_all.assert_not_called()
    processor.statements_fetched_repository.save_all.assert_not_called()
    uow.commit.assert_called_once()


def test_finalize_nsd_persists_raw_level_when_requested() -> None:
    processor, _ = _build_processor()
    processor.company_repository.iter_existing_by_columns.return_value = []
    aggregator = processor._create_aggregator()
    aggregator.add_raw_many([_make_raw()])
    uow = MagicMock()

    processor._finalize_nsd(
        nsd=_make_nsd(),
        aggregator=aggregator,
        uow=uow,
        include_raw=True,
    )

    processor.nsd_repository.save_all.assert_called_once()
    processor.statements_raw_repository.save_all.assert_called_once()
    processor.statements_fetched_repository.save_all.assert_not_called()
    uow.commit.assert_called_once()


def test_finalize_nsd_persists_processed_level_when_requested() -> None:
    processor, _ = _build_processor()
    processor.company_repository.iter_existing_by_columns.return_value = []
    aggregator = processor._create_aggregator()
    aggregator.add_raw_many([_make_raw()])
    aggregator.add_fetched_many([_make_fetched()])
    uow = MagicMock()

    processor._finalize_nsd(
        nsd=_make_nsd(),
        aggregator=aggregator,
        uow=uow,
        include_raw=True,
        include_fetched=True,
    )

    processor.nsd_repository.save_all.assert_called_once()
    processor.statements_raw_repository.save_all.assert_called_once()
    processor.statements_fetched_repository.save_all.assert_called_once()
    uow.commit.assert_called_once()


def test_build_download_extra_formats_metrics() -> None:
    processor, _ = _build_processor()
    processor.scraper_nsd.metrics_collector = SimpleNamespace(
        download_bytes=1024,
        network_bytes=10_485_760,
    )

    extra = processor._build_download_extra()

    assert extra == {
        "Download": "1.00KB",
        "Total download": "10.00MB",
    }


def test_build_download_extra_accepts_custom_scraper() -> None:
    processor, _ = _build_processor()
    scraper = SimpleNamespace(
        metrics_collector=SimpleNamespace(download_bytes=512, network_bytes=2048)
    )

    extra = processor._build_download_extra(scraper=scraper)

    assert extra == {
        "Download": "512.00B",
        "Total download": "2.00KB",
    }


class _DummyAction:
    def __init__(self, raw: bool) -> None:
        self._raw = raw

    def is_raw(self) -> bool:
        return self._raw


def test_process_statement_nsd_logs_raw_stage_with_download_extra() -> None:
    processor, logger = _build_processor()
    logger.reset_mock()

    nsd_collector = SimpleNamespace(download_bytes=0, network_bytes=0)

    def add_bytes(amount: int) -> None:
        nsd_collector.download_bytes = amount
        nsd_collector.network_bytes += amount

    nsd_collector.add_network_bytes = add_bytes  # type: ignore[attr-defined]

    processor.scraper_nsd.metrics_collector = nsd_collector
    processor.scraper_statements_raw.metrics_collector = nsd_collector

    def _fetch_raw(task: WorkerTaskDTO) -> Mapping[str, Sequence[StatementRawDTO]]:
        add_bytes(2048)
        return {"items": [_make_raw()]}

    processor.scraper_statements_raw.fetch.side_effect = _fetch_raw
    add_bytes(1024)
    download_extra = processor._build_download_extra(
        scraper=processor.scraper_nsd,
    )
    processor.policy.normalize_quarter.return_value = SimpleNamespace(
        year=2020, month=3, is_december=False
    )
    processor.policy.compute_recency_window.return_value = SimpleNamespace(
        is_recent=False
    )
    processor.policy.decide_action.return_value = _DummyAction(raw=True)

    processor._finalize_nsd = MagicMock()
    aggregator = MagicMock()
    task = WorkerTaskDTO(index=0, data="payload", worker_id="worker", total_size=1)
    progress = {"index": 0, "size": 1, "start_time": 0.0}

    processor._process_statement_nsd(
        nsd=_make_nsd(),
        task=task,
        progress=progress,
        aggregator=aggregator,
        uow=MagicMock(),
        timeline=None,
        download_extra=download_extra,
    )

    raw_call = next(
        kwargs
        for args, kwargs in logger.log.call_args_list
        if args and args[0] == "RAW 123"
    )

    assert raw_call["extra"] == {
        "Download": "2.00KB",
        "Total download": "3.00KB",
    }


def test_process_statement_nsd_logs_ftd_stage_with_raw_download_extra() -> None:
    processor, logger = _build_processor()
    logger.reset_mock()

    nsd_collector = SimpleNamespace(download_bytes=0, network_bytes=0)

    def add_bytes(amount: int) -> None:
        nsd_collector.download_bytes = amount
        nsd_collector.network_bytes += amount

    nsd_collector.add_network_bytes = add_bytes  # type: ignore[attr-defined]

    processor.scraper_nsd.metrics_collector = nsd_collector
    processor.scraper_statements_raw.metrics_collector = nsd_collector

    def _fetch_raw(task: WorkerTaskDTO) -> Mapping[str, Sequence[StatementRawDTO]]:
        add_bytes(3072)
        return {"items": [_make_raw()]}

    processor.scraper_statements_raw.fetch.side_effect = _fetch_raw
    add_bytes(2048)
    download_extra = processor._build_download_extra(
        scraper=processor.scraper_nsd,
    )
    processor.policy.normalize_quarter.return_value = SimpleNamespace(
        year=2020, month=3, is_december=False
    )
    processor.policy.compute_recency_window.return_value = SimpleNamespace(
        is_recent=True
    )
    processor.policy.decide_action.return_value = _DummyAction(raw=False)
    processor.statements_raw_repository.get_company_year_view.return_value = []
    processor.policy.version_deduplicate.return_value = []
    processor.financial_normalizer.quarterize.return_value = []
    processor.financial_normalizer.standardize.return_value = []
    processor._filter_new_fetched = MagicMock(return_value=[])

    processor._finalize_nsd = MagicMock()
    aggregator = MagicMock()
    task = WorkerTaskDTO(index=0, data="payload", worker_id="worker", total_size=1)
    progress = {"index": 0, "size": 1, "start_time": 0.0}

    processor._process_statement_nsd(
        nsd=_make_nsd(),
        task=task,
        progress=progress,
        aggregator=aggregator,
        uow=MagicMock(),
        timeline=None,
        download_extra=download_extra,
    )

    ftd_call = next(
        kwargs
        for args, kwargs in logger.log.call_args_list
        if args and args[0] == "FTD 123"
    )

    assert ftd_call["extra"] == {
        "Download": "3.00KB",
        "Total download": "5.00KB",
    }
