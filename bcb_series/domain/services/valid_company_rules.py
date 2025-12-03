"""Pure domain rules for validating companies."""

from __future__ import annotations

import re
from typing import Iterable, Sequence, Tuple

_TICKER_PATTERN = re.compile(r"^[A-Z]{4}\d{1,2}[A-Z]?$")


def _normalize_tickers(codes: Iterable[str]) -> Tuple[str, ...]:
    """Normalize raw ticker codes into a deterministic tuple of candidates."""

    seen: set[str] = set()
    normalized: list[str] = []

    for raw in codes:
        if not raw:
            continue

        ticker = str(raw).strip().upper()
        if not ticker or not _TICKER_PATTERN.match(ticker):
            continue

        if ticker in seen:
            continue

        seen.add(ticker)
        normalized.append(ticker)

    return tuple(normalized)


def decide_valid_company(
    *,
    has_statements: bool,
    candidate_tickers: Sequence[str],
    available_quote_tickers: Iterable[str],
) -> tuple[bool, Tuple[str, ...], str]:
    """Evaluate if a company should be considered valid.

    Args:
        has_statements: Whether the company has any financial statements.
        candidate_tickers: Raw ticker codes associated with the company.
        available_quote_tickers: Tickers with available stock quote data.

    Returns:
        Tuple with validity flag, normalized tickers and textual reason.
    """

    if not has_statements:
        return False, tuple(), "missing_statements"

    normalized = _normalize_tickers(candidate_tickers)
    if not normalized:
        return False, tuple(), "no_valid_tickers"

    available_set = {str(t).strip().upper() for t in available_quote_tickers if t}
    valid_tickers = tuple(t for t in normalized if t in available_set)

    if not valid_tickers:
        return False, tuple(), "no_quotes_available"

    return True, valid_tickers, "statements_and_quotes"
