# infrastructure/adapters/symbol_mapping.py
from __future__ import annotations


def b3_to_yahoo(symbol: str) -> str:
    normalized = symbol or ""
    normalized = normalized.strip().upper()
    return normalized if normalized.endswith(".SA") else f"{normalized}.SA"
