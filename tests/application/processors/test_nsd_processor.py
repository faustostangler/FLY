from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import application.processors.nsd_processor as nsd_module
from application.processors.nsd_processor import NsdProcessor, _StageTimeline
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


def test_stage_timeline_summary_tracks_elapsed(monkeypatch) -> None:
    timeline = _StageTimeline(started_at=0.0)
    perf_counter_values = iter([0.5, 2.5])
    monkeypatch.setattr(nsd_module.time, "perf_counter", lambda: next(perf_counter_values))

    first = timeline.mark("NSD")
    second = timeline.mark("RAW")

    assert first == "pipeline: nsd=500ms"
    assert second == "pipeline: nsd=500ms raw=0h00m02s"
