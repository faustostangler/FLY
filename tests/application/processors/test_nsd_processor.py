from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from application.processors.nsd_processor import NsdProcessor
from domain.dtos.worker_task_dto import WorkerTaskDTO


def _build_processor() -> NsdProcessor:
    config = SimpleNamespace(fly_settings=SimpleNamespace(app_name="TestApp"))

    return NsdProcessor(
        config=config,
        logger=MagicMock(),
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


def test_resolve_progress_start_time_reuses_first_value() -> None:
    processor = _build_processor()

    first = processor._resolve_progress_start_time(100.0)
    second = processor._resolve_progress_start_time(150.0)

    assert first == second == 100.0


def test_resolve_progress_start_time_resets_when_requested() -> None:
    processor = _build_processor()

    processor._resolve_progress_start_time(50.0)
    updated = processor._resolve_progress_start_time(200.0, reset=True)

    assert updated == 200.0


def test_build_progress_payload_defaults_total_size_when_missing() -> None:
    processor = _build_processor()
    task = WorkerTaskDTO(index=4, data="payload", worker_id="worker", total_size=None)

    payload = processor._build_progress_payload(task=task, start_time=123.456)

    assert payload["size"] == 5
    assert payload["index"] == 4
    assert payload["start_time"] == 123.456


def test_log_stage_uses_existing_progress_formatter_payload() -> None:
    processor = _build_processor()
    processor.logger.reset_mock()

    nsd = SimpleNamespace(
        nsd="123",
        quarter="2010-12-31",
        sent_date="2010-04-20 09:35:15",
        version=1,
        nsd_type="FORM",
        company_name="Example SA",
    )

    progress = {"index": 0, "size": 10, "start_time": 42.0}

    processor._log_stage("NSD", nsd, progress=progress, worker_id="worker")

    processor.logger.log.assert_called_once()
    _, kwargs = processor.logger.log.call_args

    assert kwargs["progress"]["stage"] == "NSD"
    assert kwargs["progress"]["extra_info"] == [
        "123 2010-12-31 | 2010-04-20 09:35:15 v1 | FORM Example SA"
    ]
