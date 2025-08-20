from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, TypeVar, Any, Dict

T = TypeVar("T")

@dataclass(frozen=True)
class FetchResultDTO(Generic[T]):
    items: List[T]
    total_pages: int
    download_size: int

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "FetchResultDTO[Any]":
        return FetchResultDTO(
            items=d.get("items", []),
            total_pages=int(d.get("total_pages", 1)),
            download_size=int(d.get("download_size", 1)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"items": self.items, "total_pages": self.total_pages, "download_size": self.download_size}
