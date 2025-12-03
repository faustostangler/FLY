import random
import time
from typing import Optional

import psutil

from domain.ports import ConfigPort


class TimeUtils:
    """Helper for dynamic sleep intervals based on CPU usage."""

    def __init__(self, config: ConfigPort) -> None:
        self.config = config

    def sleep_dynamic(
        self,
        wait: Optional[float] = None,
        cpu_interval: Optional[float] = None,
        multiplier: Optional[int] = 1,
    ) -> float:
        """Sleep for a dynamically adjusted time based on CPU utilization.

        The logic adjusts the delay as follows:
        - High CPU (>80%): randomly increases the wait time.
        - Medium CPU (50–80%): moderate delay.
        - Low CPU (<50%): short delay.

        Args:
            wait: Base wait time in seconds.
            cpu_interval: Sampling interval for ``psutil.cpu_percent``.
        """
        wait = wait or self.config.global_settings.wait or 2
        cpu_usage = psutil.cpu_percent(interval=cpu_interval or 0.25)

        if cpu_usage > 50:
            wait *= random.uniform(0.3, 1.5)
        elif cpu_usage > 5:
            wait *= random.uniform(0.2, 1.0)
        else:
            wait *= random.uniform(0.1, 0.5)

        wait_multiplier = wait**multiplier if multiplier else wait
        wait_multiplier = wait * multiplier if multiplier else wait

        time.sleep(wait_multiplier)

        return float(wait_multiplier)
