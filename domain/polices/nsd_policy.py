from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, Sequence, Tuple

from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.statement_raw_dto import StatementRawDTO


class NsdPolicyPort(Protocol):
    def identify_type(self, nsd: NsdDTO) -> "NsdTypePolicy": ...
    def normalize_quarter(self, nsd: NsdDTO) -> "QuarterPolicy": ...
    def compute_recency_window(self, when: date) -> "RecencyPolicy": ...
    def decide_action(self, *, year: int, quarter: int, version: int, is_december: bool, is_recent: bool) -> "ActionPolicy": ...
    def version_deduplicate(self, raws: Sequence[StatementRawDTO]) -> Sequence[StatementRawDTO]: ...


@dataclass(frozen=True)
class NsdTypePolicy:
    is_statement: bool


@dataclass(frozen=True)
class QuarterPolicy:
    year: int
    quarter: int
    is_december: bool


@dataclass(frozen=True)
class RecencyPolicy:
    is_recent: bool


@dataclass(frozen=True)
class ActionPolicy:
    kind: str  # "RAW" | "PROCESS"
    def is_raw(self) -> bool: return self.kind == "RAW"
    def is_process(self) -> bool: return self.kind == "PROCESS"


class NsdPolicy(NsdPolicyPort):
    def __init__(self, *, allowed_types: Tuple[str, ...], recency_year: int | None = None) -> None:
        self._allowed_types = allowed_types
        self._recency_year = recency_year  # None => usa ano corrente

    # tipo suportado: compara nsd.nsd_type com config.domain.statements_types (case-insensitive)
    def identify_type(self, nsd: NsdDTO) -> NsdTypePolicy:
        return NsdTypePolicy(is_statement=(getattr(nsd, "nsd_type", "") in self._allowed_types))

    # normaliza quarter a partir de nsd.quarter (date/datetime). Fallback: year/month ou sent_date.
    def normalize_quarter(self, nsd: NsdDTO) -> QuarterPolicy:
        q = getattr(nsd, "quarter", None)
        if isinstance(q, (date, datetime)):
            y, m = q.year, q.month
        else:
            y = getattr(nsd, "year", None)
            m = getattr(nsd, "month", None)
            if y is None or m is None:
                sent = getattr(nsd, "sent_date", None)
                if isinstance(sent, (date, datetime)):
                    y, m = sent.year, sent.month
                else:
                    raise ValueError("NsdDTO.quarter precisa ser date/datetime ou informar year/month")
        q = 1 if m <= 3 else 2 if m <= 6 else 3 if m <= 9 else 4
        return QuarterPolicy(year=int(y), quarter=q, is_december=(m == 12))

    # recência: None => ano corrente; int => >= recency_year
    def compute_recency_window(self, when: date) -> RecencyPolicy:
        if self._recency_year is None:
            return RecencyPolicy(is_recent=(when.year == date.today().year))
        return RecencyPolicy(is_recent=(when.year >= self._recency_year))

    # decisão: v>1 processa; v1 em dezembro processa; v1 fora de dezembro processa se recente, senão RAW
    def decide_action(self, *, year: int, quarter: int, version: int, is_december: bool, is_recent: bool) -> ActionPolicy:
        if version > 1:
            return ActionPolicy("PROCESS")
        if is_december:
            return ActionPolicy("PROCESS")
        if is_recent:
            return ActionPolicy("PROCESS")
        return ActionPolicy("RAW")

    # dedup por versão: mantém a maior versão por (company_id, year, quarter, account/account_code)
    def version_deduplicate(self, raws: Sequence[StatementRawDTO]) -> Sequence[StatementRawDTO]:
        latest: dict[tuple, StatementRawDTO] = {}
        for r in raws:
            key = (
                getattr(r, "company_id", None),
                int(getattr(r, "year", 0)),
                int(getattr(r, "quarter", 0)),
                str(getattr(r, "account", getattr(r, "account_code", ""))),
            )
            cur = latest.get(key)
            rv = int(getattr(r, "version", 0))
            cv = int(getattr(cur, "version", -1)) if cur is not None else -1
            if cur is None or rv > cv:
                latest[key] = r
        return list(latest.values())
