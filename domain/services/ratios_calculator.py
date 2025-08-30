from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.dtos.raw_statement_dto import StatementRawDTO
    from domain.dtos.fetched_statement_dto import StatementFetchedDTO


@runtime_checkable
class RatiosCalculatorPort(Protocol):
    """Serviço puro que calcula métricas/ratios a partir de linhas padronizadas."""
    def calculate(self, standards: Sequence["StatementRawDTO"]) -> Sequence["StatementFetchedDTO"]: ...
