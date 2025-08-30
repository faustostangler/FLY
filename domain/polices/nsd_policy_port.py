from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol, Sequence, Dict, Tuple, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.dtos.nsd_dto import NsdDTO
    from domain.dtos.raw_statement_dto import StatementRawDTO


@dataclass(frozen=True)
class SupportedTypeVO:
    supported: bool
    type_name: str | None = None


@dataclass(frozen=True)
class QuarterVO:
    year: int
    quarter: int  # 1..4

    @property
    def is_december(self) -> bool:
        return self.quarter == 4


@dataclass(frozen=True)
class RecencyVO:
    is_recent: bool
    window_label: str  # ex.: "current_year", "none"


@dataclass(frozen=True)
class ActionVO:
    kind: str  # "RAW" | "PROCESS"

    def is_raw(self) -> bool:
        return self.kind == "RAW"

    def is_process(self) -> bool:
        return self.kind == "PROCESS"


@runtime_checkable
class NsdPolicyPort(Protocol):
    """Política composta do domínio para NSD: pura, determinística e testável."""
    def identify_type(self, nsd: "NsdDTO") -> SupportedTypeVO: ...
    def normalize_quarter(self, nsd: "NsdDTO") -> QuarterVO: ...
    def compute_recency_window(self, when: date) -> RecencyVO: ...
    def decide_action(
        self, *, year: int, quarter: int, version: int, is_december: bool, is_recent: bool
    ) -> ActionVO: ...
    def version_deduplicate(self, raws: Sequence["StatementRawDTO"]) -> Sequence["StatementRawDTO"]: ...


class NsdPolicyDefault(NsdPolicyPort):
    """Implementação padrão que codifica exatamente suas regras declaradas."""
    def __init__(self, *, supported_types: set[str] | None = None, current_date: date | None = None) -> None:
        self._supported_types = supported_types or {"SUPPORTED"}  # ajuste conforme seu NSDDTO.type
        self._today = current_date or date.today()

    def identify_type(self, nsd: "NsdDTO") -> SupportedTypeVO:
        # Suporte binário por nome. Adapte ao seu DTO real.
        tname = getattr(nsd, "type", None)
        return SupportedTypeVO(supported=bool(tname in self._supported_types), type_name=tname)

    def normalize_quarter(self, nsd: "NsdDTO") -> QuarterVO:
        # Normaliza a partir de nsd.period (ex.: "2011-03", "2010-12")
        period = getattr(nsd, "period", None)
        print(f'period already normalized? {period}')
        if not period or len(period) < 7:
            raise ValueError("NSD sem período normalizável")
        year = int(period[0:4])
        month = int(period[5:7])
        q = ((month - 1) // 3) + 1
        return QuarterVO(year=year, quarter=q)

    def compute_recency_window(self, when: date) -> RecencyVO:
        # “Recente” = ano do NSD igual ao ano corrente
        is_recent = when.year == self._today.year
        return RecencyVO(is_recent=is_recent, window_label="current_year" if is_recent else "none")

    def decide_action(
        self, *, year: int, quarter: int, version: int, is_december: bool, is_recent: bool
    ) -> ActionVO:
        # Regras:
        # v>1 => PROCESS
        # v1 e dezembro => PROCESS
        # v1 fora de dez => PROCESS se recente; caso contrário RAW
        if version > 1:
            return ActionVO("PROCESS")
        if version == 1 and is_december:
            return ActionVO("PROCESS")
        if version == 1 and is_recent:
            return ActionVO("PROCESS")
        return ActionVO("RAW")

    def version_deduplicate(self, raws: Sequence["StatementRawDTO"]) -> Sequence["StatementRawDTO"]:
        # Mantém a maior versão por (company, year, quarter, account_code)
        latest: Dict[Tuple[str, int, int, str], "StatementRawDTO"] = {}
        for r in raws:
            key = (r.company_id, r.year, r.quarter, r.account_code)
            if key not in latest or r.version > latest[key].version:
                latest[key] = r
        return tuple(latest.values())
