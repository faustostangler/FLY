import time


class ProgressFormatter:
    """Format progress information for logging."""

    def format(self, progress: dict) -> str:
        """Return a formatted progress string like ``"15/100 | 15.00% | 0h00m10s + 0h01m00s = 0h01m10s"``."""
        try:
            index = progress.get("index", 0)
            size = progress.get("size", 1)
            start = progress.get("start_time", time.perf_counter())
            now = time.perf_counter()

            completed = index + 1
            percent = completed / size
            elapsed = now - start
            avg = elapsed / completed
            remaining = (size - completed) * avg
            total_est = elapsed + remaining

            def fmt(seconds):
                h, rem = divmod(int(seconds), 3600)
                m, s = divmod(rem, 60)
                return f"{h}h{m:02}m{s:02}s"

            base = f"{size - completed}+{completed}={size} | {percent:.2%} | {fmt(remaining)} + {fmt(elapsed)} = {fmt(total_est)}"

            extra_info = progress.get("extra_info", [])
            if isinstance(extra_info, list):
                extra_str = " ".join(str(e) for e in extra_info if e)
                return f"{base} | {extra_str}" if extra_str else base
            return base
        except Exception:
            return ""
