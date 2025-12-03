"""Utilities for hashing statement data."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import List

from domain.dto.statement_raw_dto import StatementRawDTO

from .math_utils import parse_quarter


def compute_hash(raw_dtos: List[StatementRawDTO]) -> str:
    """Return SHA256 hash for ``raw_dtos`` sorted by account and date."""

    def sort_key(dto: StatementRawDTO) -> tuple:
        dt = parse_quarter(dto.quarter)
        year = dt.year if dt else 0
        quarter = dto.quarter or ""
        return dto.account, year, quarter

    sorted_dtos = sorted(raw_dtos, key=sort_key)
    joined = "".join(str(asdict(dto)) for dto in sorted_dtos)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
