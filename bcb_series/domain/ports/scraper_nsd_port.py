"""Port definitions for external NSD data providers."""

from __future__ import annotations

from typing import Iterable, List, Optional

from domain.dtos.nsd_dto import NsdDTO
from domain.ports.scraper_base_port import ScraperBasePort

# T = TypeVar("T")


class ScraperNsdPort(ScraperBasePort[NsdDTO]):
    """Port for external NSD data providers."""
    def iter_nsd(
        self,
        *,
        start: int = 1,
        threshold: Optional[int] = None,
        existing_codes: Optional[List[int]] = None,
        max_nsd: int = 1,
        **kwargs,
    ) -> Iterable[NsdDTO]:
        """Entrega NSDs um a um, em ordem incremental, sem materializar tudo."""
        raise NotImplementedError

    def fetch_one(self, nsd: int) -> NsdDTO | None: ...
