from __future__ import annotations

import time
from typing import Any, Mapping


class ProgressFormatter:
    """Formats progress dictionaries into concise log-friendly strings.

    This formatter expects a mapping with progress keys and renders a human-
    readable summary with counts, percentage, and time estimates.

    Example:
        "85+15=100 | 15.00% | 0h01m40s + 0h00m10s = 0h01m50s | extra info"

    Notes:
        - The input mapping is treated defensively; missing values fall back
          to safe defaults.
        - Any exception during formatting results in an empty string to avoid
          breaking logging pipelines.
    """

    def format(self, progress: Mapping[str, Any]) -> str:
        """Build a formatted progress line.

        Args:
            progress (Mapping[str, Any]): A mapping with optional keys:
                - "index" (int): Zero-based index of the current item.
                - "size" (int): Total number of items to process.
                - "start_time" (float): Monotonic start timestamp (perf_counter).
                - "extra_info" (list[Any]): Optional extra tokens appended at end.

        Returns:
            str: A string like
                "85+15=100 | 15.00% | 0h01m40s + 0h00m10s = 0h01m50s"
                optionally followed by " | " + joined extra info.
                Returns an empty string on failure.

        """
        try:
            # Read basic counters and provide defensive defaults
            index = progress.get("index", 0)
            size = progress.get("size", 1)
            start = progress.get("start_time", time.perf_counter())
            now = time.perf_counter()

            # Convert zero-based index to completed count
            completed = index + 1

            # Compute fraction complete
            percent = completed / size

            # Measure elapsed time since start
            elapsed = now - start

            # Estimate average time per item
            avg = elapsed / completed

            # Estimate remaining and total durations
            remaining = (size - completed) * avg
            total_est = elapsed + remaining

            # Format seconds as "HhMMmSSs"
            def fmt(seconds):
                h, rem = divmod(int(seconds), 3600)
                m, s = divmod(rem, 60)
                return f"{h}h{m:02}m{s:02}s"

            # Build the base progress string with counts, percent, and times
            base = (
                f"{size - completed}+{completed}={size} | "
                f"{percent:.2%} | {fmt(remaining)} + {fmt(elapsed)} = {fmt(total_est)}"
            )

            # Optionally append extra info tokens if provided as a list
            extra_info = progress.get("extra_info", [])
            if isinstance(extra_info, list):
                # Join non-empty tokens with spaces
                extra_str = " ".join(str(e) for e in extra_info if e)
                return f"{base} | {extra_str}" if extra_str else base

            # Return base string when extra_info is not a list
            return base
        except Exception:
            # Fail-safe: never raise from a formatter used in logging paths
            return ""
