"""Port definitions for external NSD data providers."""

from __future__ import annotations

from typing import Callable, List, Optional, TypeVar

from domain.dto import ExecutionResultDTO, NsdDTO

from .base_scraper_port import BaseScraperPort

T = TypeVar("T")


class NSDSourcePort(BaseScraperPort[NsdDTO]):
    """Port for external NSD data providers."""

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        skip_codes: Optional[List[str]] = None,
        save_callback: Optional[Callable[[List[NsdDTO]], None]] = None,
        start: int = 1,
        max_nsd: Optional[int] = None,
        **kwargs,
    ) -> ExecutionResultDTO[NsdDTO]:
        raise NotImplementedError
