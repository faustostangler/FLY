# # domain/policies/nsd_policy.py
# from __future__ import annotations

# from dataclasses import dataclass
# from datetime import date, datetime
# from typing import Protocol, Sequence, Tuple, Iterable, Dict

# from domain.dtos.nsd_dto import NsdDTO
# from domain.dtos.statement_raw_dto import StatementRawDTO


# # ----------------- Tipos de retorno explícitos -----------------

# @dataclass(frozen=True)
# class TypeSupport:
#     is_statement: bool
#     reason: str = ""

# @dataclass(frozen=True)
# class QuarterPolicy:
#     year: int
#     quarter: int
#     is_december: bool

# @dataclass(frozen=True)
# class RecencyPolicyWindow:
#     is_recent: bool
#     basis_year: int

# @dataclass(frozen=True)
# class ActionPolicy:
#     kind: str  # "RAW" ou "PROCESS"
#     def is_raw(self) -> bool: return self.kind == "RAW"
#     def is_process(self) -> bool: return self.kind == "PROCESS"


# # ----------------- Porta -----------------

# class NsdPolicyPort(Protocol):
#     def identify_type(self, nsd: NsdDTO) -> TypeSupport: ...
#     def normalize_quarter(self, nsd: NsdDTO) -> QuarterPolicy: ...
#     def compute_recency_window(self, when: date) -> RecencyPolicyWindow: ...
#     def decide_action(self, *, year: int, quarter: int, version: int, is_december: bool, is_recent: bool) -> ActionPolicy: ...
#     def version_deduplicate(self, raws: Sequence[StatementRawDTO]) -> Sequence[StatementRawDTO]: ...


# # ----------------- Implementação concreta -----------------

# class NsdPolicy(NsdPolicyPort):
#     """
#     Regras:
#       - identify_type: nsd.nsd_type precisa estar em allowed_types (comparação uppercase, strip).
#       - normalize_quarter: extrai (ano, quarter) de nsd.quarter (datetime ou date). is_december se month == 12.
#       - compute_recency_window:
#           * se recency_year for None: recente == (when.year == hoje.year)
#           * se recency_year for int:  recente == (when.year >= recency_year)
#       - decide_action:
#           * version > 1 => PROCESS
#           * version == 1 and is_december => PROCESS
#           * version == 1 and not is_december => PROCESS se is_recent, senão RAW
#       - version_deduplicate: para cada (company_id, year, quarter, account_code) mantém a maior versão.
#     """

#     def __init__(self, *, allowed_types: Tuple[str, ...] | None = None, recency_year: int | None = None) -> None:
#         self.allowed_types = tuple(t.strip().upper() for t in (allowed_types or (
#             "DEMONSTRACOES FINANCEIRAS PADRONIZADAS",
#             "INFORMACOES TRIMESTRAIS",
#         )))
#         self.recency_year = recency_year

#     # ---- tipo suportado

#     def identify_type(self, nsd: NsdDTO) -> TypeSupport:
#         nsd_type = (getattr(nsd, "nsd_type", "") or "").strip().upper()
#         ok = nsd_type in self.allowed_types
#         return TypeSupport(supported=ok, reason="" if ok else f"nsd_type '{nsd_type}' não suportado")

#     # ---- quarter

#     def normalize_quarter(self, nsd: NsdDTO) -> QuarterPolicy:
#         qdt = getattr(nsd, "quarter", None)
#         if not isinstance(qdt, (datetime, date)):
#             raise ValueError("nsd.quarter precisa ser datetime/date para normalização")
#         y = qdt.year
#         m = qdt.month
#         q = 1 if m <= 3 else 2 if m <= 6 else 3 if m <= 9 else 4
#         return QuarterPolicy(year=y, quarter=q, is_december=(m == 12))

#     # ---- recência

#     def compute_recency_window(self, when: date) -> RecencyPolicyWindow:
#         today = date.today()
#         if self.recency_year is None:
#             return RecencyPolicyWindow(is_recent=(when.year == today.year), basis_year=today.year)
#         return RecencyPolicyWindow(is_recent=(when.year >= self.recency_year), basis_year=self.recency_year)

#     # ---- decisão

#     def decide_action(self, *, year: int, quarter: int, version: int, is_december: bool, is_recent: bool) -> ActionPolicy:
#         if version > 1:
#             return ActionPolicy("PROCESS")
#         if is_december:
#             return ActionPolicy("PROCESS")
#         if is_recent:
#             return ActionPolicy("PROCESS")
#         return ActionPolicy("RAW")

#     # ---- deduplicação por versão

#     def version_deduplicate(self, raws: Sequence[StatementRawDTO]) -> Sequence[StatementRawDTO]:
#         best: Dict[tuple, StatementRawDTO] = {}
#         for r in raws:
#             key = (
#                 getattr(r, "company_id", None),
#                 int(getattr(r, "year", 0)),
#                 int(getattr(r, "quarter", 0)),
#                 # use o campo de conta que você realmente tem no DTO
#                 getattr(r, "account_code", None) or getattr(r, "account", None),
#             )
#             cur = best.get(key)
#             if cur is None or int(getattr(r, "version", 0)) > int(getattr(cur, "version", 0)):
#                 best[key] = r
#         return list(best.values())
