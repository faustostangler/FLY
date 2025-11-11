"""Authentication dependencies for FastAPI routers."""

from __future__ import annotations

from typing import Any, Dict


def get_current_user() -> Dict[str, Any]:
    """Return a placeholder authenticated user.

    This stub keeps the router signature aligned with authenticated endpoints
    and can be replaced by a real authentication backend when available.
    """

    return {"sub": "anonymous"}
