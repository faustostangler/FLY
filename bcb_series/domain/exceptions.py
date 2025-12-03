"""Domain-level exception hierarchy."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for domain/business rule violations."""


__all__ = ["DomainError"]

