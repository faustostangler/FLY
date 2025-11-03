"""Application service layer helpers with lazy imports."""

__all__ = ["CacheRatiosService"]


def __getattr__(name: str):  # pragma: no cover - delegation helper
    if name == "CacheRatiosService":
        from application.services.cache_ratios_service import CacheRatiosService

        return CacheRatiosService
    raise AttributeError(name)
