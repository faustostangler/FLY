# domain/services/financial_normalizer.py
from __future__ import annotations

from dataclasses import is_dataclass, replace
from datetime import datetime
# from decimal import Decimal
from typing import Any, Callable, Dict, Iterable, List, Sequence

from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.statement_raw_dto import StatementRawDTO


class FinancialNormalizerPort:
    """Serviço puro de domínio: recebe RAW (ano, companhia) já deduplicado por versão,
    aplica a matemática de quarter e depois o 'intel' do legado, emitindo FETCHED."""
    def standardize(self, raws: Sequence[StatementRawDTO]) -> Sequence[StatementFetchedDTO]:
        raise NotImplementedError


class FinancialNormalizer(FinancialNormalizerPort):
    """Implementação que reaproveita o 'intel' do legado.
    Ordem correta: matemágica de quarter em todas as contas, depois classificação ('intel')."""

    def __init__(
        self,
        *,
        # fetched_builder: Callable[[StatementRawDTO, str, Decimal], StatementFetchedDTO] | None = None,
        fetched_builder: Callable[[StatementRawDTO, str, float], StatementFetchedDTO] | None = None,
        intel_module_path: str = "domain.utils.intel",
    ) -> None:
        self._build_fetched = fetched_builder or self._default_builder
        self._intel_module_path = intel_module_path

    def standardize(self, raws: Sequence[StatementRawDTO]) -> Sequence[StatementFetchedDTO]:
        quarterized = list(self._apply_quarter_math(raws))
        fetched = self._classify_with_intel(quarterized)
        return fetched

    # ---------- 1) Matemática de quarter sobre RAW do ano deduplicado ----------
    # Caminho ATUAL: usa DATA do quarter; identifica pelo mês (03, 06, 09, 12) e converte acumulados conforme regras.
    def _apply_quarter_math(self, raws: Sequence[StatementRawDTO]) -> Iterable[StatementRawDTO]:
        # agrupa por (company, ano, conta) e indexa por mês do quarter {3,6,9,12}
        groups: dict[tuple[str | None, int, str], dict[int, StatementRawDTO]] = {}
        for r in raws:
            d: datetime = r.quarter
            y, m = d.year, d.month
            key = (r.company_name, y, self._account_of(r))
            groups.setdefault(key, {})[m] = r  # meses 3,6,9,12

        # 3) aplica regras preservando ordem dos meses
        for (company_name, year, account), mmap in groups.items():
            family = (account or "")[:1]

            # qmap com meses reais como chaves (3, 6, 9, 12)
            qmap: dict[int, StatementRawDTO] = {int(m): row for m, row in mmap.items()}

            if family in {"6", "7"}:
                yield from self._diff_quarters(qmap)
            elif family in {"3", "4"}:
                yield from self._adjust_q4(qmap)
            else:
                yield from self._copy(qmap)

    @staticmethod
    # def _default_builder(raw: StatementRawDTO, target_line: str, value: Decimal) -> StatementFetchedDTO:
    def _default_builder(raw: StatementRawDTO, target_line: str, value: float) -> StatementFetchedDTO:
        # quarter como texto YYYY-MM (mês do quarter)
        q: datetime = raw.quarter
        ver = getattr(raw, "version", None)
        ver_str = str(ver) if ver is not None else None

        return StatementFetchedDTO(
            id=None,
            nsd=str(getattr(raw, "nsd", "")),
            company_name=getattr(raw, "company_name", None),
            quarter=q,  # data normalizada YYYY-MM
            version=ver_str,
            grupo=str(getattr(raw, "grupo", "")),
            quadro=str(getattr(raw, "quadro", "")),
            account=str(getattr(raw, "account", getattr(raw, "account_code", ""))),
            description=str(getattr(raw, "description", "")),
            value=float(value),
            processing_hash="",
        )

    # def _diff_quarters(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
    #     prev = None
    #     for m in (3, 6, 9, 12):
    #         r = qmap.get(m)
    #         if r is None:
    #             continue
    #         cur = float(getattr(r, "value", 0.0) or 0.0)
    #         out_val = cur if prev is None else cur - prev
    #         prev = cur
    #         yield self._with_value(r, self._dec(out_val))

    def _diff_quarters(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
        prev = None
        for m in (3, 6, 9, 12):
            r = qmap.get(m)
            if r is None:
                continue
            cur = float(getattr(r, "value", 0.0) or 0.0)
            out_val = cur if prev is None else cur - prev
            prev = cur
            yield self._with_value(r, float(out_val))

    # def _adjust_q4(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
    #     m3, m6, m9, m12 = qmap.get(3), qmap.get(6), qmap.get(9), qmap.get(12)

    #     for r in (m3, m6, m9):
    #         if r is not None:
    #             yield r

    #     if m12 is not None:
    #         s3 = float(getattr(m3, "value", 0.0) or 0.0) if m3 else 0.0
    #         s6 = float(getattr(m6, "value", 0.0) or 0.0) if m6 else 0.0
    #         s9 = float(getattr(m9, "value", 0.0) or 0.0) if m9 else 0.0
    #         v12 = float(getattr(m12, "value", 0.0) or 0.0)
    #         yield self._with_value(m12, self._dec(v12 - (s3 + s6 + s9)))

    def _adjust_q4(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
        m3, m6, m9, m12 = qmap.get(3), qmap.get(6), qmap.get(9), qmap.get(12)

        for r in (m3, m6, m9):
            if r is not None:
                yield r

        if m12 is not None:
            s3 = float(getattr(m3, "value", 0.0) or 0.0) if m3 else 0.0
            s6 = float(getattr(m6, "value", 0.0) or 0.0) if m6 else 0.0
            s9 = float(getattr(m9, "value", 0.0) or 0.0) if m9 else 0.0
            v12 = float(getattr(m12, "value", 0.0) or 0.0)
            yield self._with_value(m12, float(v12 - (s3 + s6 + s9)))

    # def _copy(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
    #     for q in sorted(qmap):
    #         r = qmap[q]
    #         val_raw = getattr(r, "value", 0.0)
    #         if not isinstance(val_raw, (int, float, str, Decimal)):
    #             raise TypeError(f"Unexpected value type for 'value': {type(val_raw).__name__}")
    #         yield self._with_value(r, self._dec(val_raw))

    def _copy(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
        for q in sorted(qmap):
            r = qmap[q]
            val_raw = getattr(r, "value", 0.0)
            # if not isinstance(val_raw, (int, float, str, Decimal)):
            if not isinstance(val_raw, (int, float, str)):
                raise TypeError(f"Unexpected value type for 'value': {type(val_raw).__name__}")
            yield self._with_value(r, float(val_raw))

    # ---------- 2) 'Intel': classifica e gera FETCHED ----------
    def _classify_with_intel(self, rows: Sequence[StatementRawDTO]) -> List[StatementFetchedDTO]:
        try:
            from importlib import import_module
            intel = import_module(self._intel_module_path)

            def normalize_account(val: str) -> str:
                parts = [(p.lstrip("0") or "0") for p in (val or "").split(".")]
                return ".".join(seg.zfill(2) for seg in parts)

            def account_of_raw(r: StatementRawDTO) -> str:
                # Suporta tanto raw.account quanto raw.account_code
                return getattr(r, "account_code", None) or getattr(r, "account", "") or ""

            def matches(row: StatementRawDTO, crit: list[tuple[str, str, Any]]) -> bool:
                for column, cond, needle in crit:
                    raw_val = getattr(row, column, None)
                    if raw_val is None and column == "account":
                        raw_val = account_of_raw(row)
                    value = str(raw_val or "").lower()

                    if column in ("account", "account_code"):
                        v_cmp = normalize_account(value)
                        n_cmp = normalize_account(str(needle))
                    else:
                        v_cmp = value
                        n_cmp = str(needle).lower()

                    bag = needle if isinstance(needle, (list, tuple)) else [needle]
                    bag = [str(x).lower() for x in bag]

                    if cond == "equals":
                        if v_cmp != n_cmp:
                            return False
                    elif cond == "not_equals":
                        if v_cmp == n_cmp:
                            return False
                    elif cond == "startswith":
                        if not v_cmp.startswith(n_cmp):
                            return False
                    elif cond == "contains_any":
                        if not any(tok in value for tok in bag):
                            return False
                    elif cond in ("contains_all",):
                        if not all(tok in value for tok in bag):
                            return False
                    elif cond in ("not_contains", "contains_none"):
                        if any(tok in value for tok in bag):
                            return False
                    elif cond == "level":
                        level = value.count(".") + 1 if value else 1
                        needle_val = needle[0] if isinstance(needle, (list, tuple)) and needle else needle
                        try:
                            expected = needle_val  # int(needle_val)
                        except Exception:
                            return False
                        if level != expected:
                            return False

                return True

            def map_node(d: dict):
                return {
                    "target_line": d.get("target_line", ""),
                    "criteria": [tuple(c) for c in d.get("criteria", [])],
                    "children": [map_node(c) for c in d.get("sub_criteria", [])],
                }

            roots: list[dict] = []
            for name in dir(intel):
                if name.endswith("_criteria"):
                    value = getattr(intel, name)
                    if isinstance(value, list):
                        roots.extend(map(map_node, value))

            def walk(node: dict, universe: list[StatementRawDTO]) -> list[StatementFetchedDTO]:
                hits = [r for r in universe if matches(r, node["criteria"])]
                fetched: list[StatementFetchedDTO] = []
                for r in hits:
                    val_raw = getattr(r, "value", 0.0)
                    # if not isinstance(val_raw, (int, float, str, Decimal)):
                    if not isinstance(val_raw, (int, float, str)):
                        raise TypeError(f"Unexpected value type for 'value': {type(val_raw).__name__}")
                    val = float(val_raw)
                    fetched.append(self._build_fetched(r, node["target_line"], val))

            # def walk(node: dict, universe: list[StatementRawDTO]) -> list[StatementFetchedDTO]:
            #     hits = [r for r in universe if matches(r, node["criteria"])]
            #     fetched: list[StatementFetchedDTO] = []
            #     for r in hits:
            #         val_raw = getattr(r, "value", 0.0)
            #         if not isinstance(val_raw, (int, float, str, Decimal)):
            #             raise TypeError(f"Unexpected value type for 'value': {type(val_raw).__name__}")
            #         val = self._dec(val_raw)
            #         fetched.append(self._build_fetched(r, node["target_line"], val))
                parents = {normalize_account(getattr(f, "account_code", "")) for f in fetched}
                if not parents:
                    return fetched
                children_rows = [r for r in universe if any(normalize_account(account_of_raw(r)).startswith(p) for p in parents)]
                for child in node["children"]:
                    fetched.extend(walk(child, children_rows))
                return fetched

            out: list[StatementFetchedDTO] = []
            for node in roots:
                out.extend(walk(node, list(rows)))
            return out
        except Exception as e:
            print(e)
        return []
    # ---------- utilitários ----------
    # @staticmethod
    # def _dec(x: Any) -> Decimal:
    #     if isinstance(x, Decimal):
    #         return x
        
    #     if isinstance(x, (int, float, str)):
    #         return Decimal(str(x))
        
    #     try:
    #         return Decimal(x)
    #     except Exception as e:
    #         raise TypeError(f"Value of type {type(x).__name__} is not convertible to Decimal.") from e

    # @staticmethod
    # def _with_value(raw: StatementRawDTO, value: Decimal) -> StatementRawDTO:
    #     if is_dataclass(raw):
    #         return replace(raw, value=value)
    #     raise TypeError("StatementRawDTO must be a dataclass to clone with a new value.")

    @staticmethod
    def _with_value(raw: StatementRawDTO, value: float) -> StatementRawDTO:
        if is_dataclass(raw):
            return replace(raw, value=float(value))
        raise TypeError("StatementRawDTO must be a dataclass to clone with a new value.")

    @staticmethod
    def _account_of(raw: StatementRawDTO) -> str:
        return getattr(raw, "account_code", None) or getattr(raw, "account", "") or ""

    # --------- [LEGACY NÃO USADO] caminho antigo baseado em ordinal de quarter ---------
    # Mantido comentado para referência. O projeto agora trabalha com datas de quarter.
    #
    # def _apply_quarter_math(self, raws: Sequence[StatementRawDTO]) -> Iterable[StatementRawDTO]:
    #     groups: Dict[Tuple[str, int, str], Dict[int, StatementRawDTO]] = {}
    #     for r in raws:
    #         key = (r.company_name, int(r.quarter.year), self._account_of(r))
    #         groups.setdefault(key, {})[int(r.quarter)] = r
    #     for (_, _, account), qmap in groups.items():
    #         family = (account or "")[:1]
    #         if family in {"6", "7"}:
    #             yield from self._diff_quarters(qmap)
    #         elif family in {"3", "4"}:
    #             yield from self._adjust_q4(qmap)
    #         else:
    #             yield from self._copy(qmap)

    # @staticmethod
    # def _default_builder(raw: StatementRawDTO, target_line: str, value: Decimal) -> StatementFetchedDTO:
    #     # Construía quarter como "Qn" (ordinal). Substituído por YYYY-MM.
    #     q = getattr(raw, "quarter", None)
    #     quarter_str = f"Q{int(q)}" if q is not None else None
    #     ver = getattr(raw, "version", None)
    #     ver_str = str(ver) if ver is not None else None
    #     return StatementFetchedDTO(
    #         id=None,
    #         nsd=str(getattr(raw, "nsd", "")),
    #         company_name=getattr(raw, "company_name", None),
    #         quarter=quarter_str,
    #         version=ver_str,
    #         grupo=str(getattr(raw, "grupo", "")),
    #         quadro=str(getattr(raw, "quadro", "")),
    #         account=str(getattr(raw, "account", getattr(raw, "account_code", ""))),
    #         description=str(getattr(raw, "description", "")),
    #         value=float(value),
    #         processing_hash="",
    #     )
