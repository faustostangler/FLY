from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from infrastructure.logging.progress_formatter import ProgressFormatter


def test_format_does_not_create_extra_pipe_tokens() -> None:
    formatter = ProgressFormatter()
    nsd_extra_info = "2020-03-31 v1 | 2020-04-20 10:30:00 | FORM Example SA"

    progress = {
        "index": 0,
        "size": 10,
        "start_time": time.perf_counter() - 1,
        "extra_info": [nsd_extra_info],
    }

    line = formatter.format(progress)
    parts = line.split(" | ")

    assert len(parts) == 3
    assert "|" not in parts[2]
    assert "2020-03-31 v1 / 2020-04-20 10:30:00 / FORM Example SA" in parts[2]
    assert parts[2].endswith(")")
