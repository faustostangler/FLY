"""Port definition for transformer configuration values."""

from __future__ import annotations

from typing import Iterable, Protocol, Tuple


class TransformersConfigPort(Protocol):
    """Expose settings for statement transformers."""

    math_year_end_prefixes: Tuple[str, ...]
    math_cumulative_prefixes: Tuple[str, ...]
    math_target_accounts: Tuple[str, ...]
    intel_year_end_prefixes: Tuple[str, ...]
    intel_cumulative_prefixes: Tuple[str, ...]
    intel_section_criteria: Tuple[Tuple[str, Iterable[dict]], ...]
