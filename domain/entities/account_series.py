from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class AccountPoint:
    """Representa um ponto da série temporal de uma conta contábil."""

    date: date
    value: float
