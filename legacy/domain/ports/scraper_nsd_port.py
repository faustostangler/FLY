"""Port definitions for external NSD data providers."""

from __future__ import annotations

from typing import Callable, List, Optional, TypeVar

from domain.dto import ExecutionResultDTO, NsdDTO

from domain.ports.scraper_base_port import ScraperBasePort

# T = TypeVar("T")


class ScraperNsdPort(ScraperBasePort[NsdDTO]):
    """Port for external NSD data providers."""

    # def fetch_nsd(
    #     self,
    #     threshold: Optional[int] = None,
    #     existing_codes: Optional[List[str]] = None,
    #     save_callback: Optional[Callable[[List[NsdDTO]], None]] = None,
    #     start: int = 1,
    #     max_nsd: Optional[int] = None,
    #     **kwargs,
    # ) -> ExecutionResultDTO[NsdDTO]:
    #     raise NotImplementedError
