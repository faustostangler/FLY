from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Sequence, runtime_checkable

if TYPE_CHECKING:
    # Evita import circular. Substitua pelos seus DTOs reais.
    from domain.dtos.statement_raw_dto import StatementRawDTO


@runtime_checkable
class YearViewPort(Protocol):
    """Porta da visão 'ano corrido' para recuperar RAW vigentes por companhia+ano."""
    def get_company_year_view(self, *, company_id: str, year: int) -> Sequence["StatementRawDTO"]: ...
