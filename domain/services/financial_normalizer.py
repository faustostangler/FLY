from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.dtos.raw_statement_dto import StatementRawDTO
    from domain.dtos.fetched_statement_dto import StatementFetchedDTO


@runtime_checkable
class FinancialNormalizerPort(Protocol):
    """Serviço puro que padroniza coleções RAW em 'standards' prontos para cálculo."""
    def standardize(self, raws: Sequence["StatementRawDTO"]) -> Sequence["StatementFetchedDTO"]: ...
