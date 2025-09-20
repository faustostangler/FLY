from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# <<<<<<< codex/fix-unrealistic-time-progression-logs-0j1j18
from application.processors.nsd_processor import NsdProcessor
# =======
# import application.processors.nsd_processor as nsd_module
# from application.processors.nsd_processor import NsdProcessor, _StageTimeline
# >>>>>>> 2025-09-09-Fetch-Adjustments
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.dtos.nsd_dto import NsdDTO
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
