"""Helpers to coerce request field names to :class:`CompanyField`."""

from __future__ import annotations

from domain.value_objects.company_filters import CompanyField


def normalize_field(value: str | None) -> CompanyField | None:
    """Map raw field names (including aliases) to :class:`CompanyField`.

    Accepts case-insensitive inputs and common aliases used by the frontend and
    CLI (e.g. ``codigo`` or ``ticker`` for ``code``).
    """

    if not value:
        return None

    normalized = value.strip().lower()
    if not normalized:
        return None

    aliases = {
        "codigo": CompanyField.CODE,
        "ticker": CompanyField.CODE,
        "code": CompanyField.CODE,
        "cnpj": CompanyField.CNPJ,
    }

    if normalized in aliases:
        return aliases[normalized]

    try:
        return CompanyField(normalized)
    except ValueError:
        return None


__all__ = ["normalize_field"]
