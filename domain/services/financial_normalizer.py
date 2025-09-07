# domain/services/financial_normalizer.py
from __future__ import annotations
from dataclasses import replace, is_dataclass
from decimal import Decimal
from datetime import datetime
from typing import Any, Iterable, List, Sequence, Dict, Tuple, Callable

from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.dtos.statement_fetched_dto import StatementFetchedDTO


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
        fetched_builder: Callable[[StatementRawDTO, str, Decimal], StatementFetchedDTO] | None = None,
        intel_module_path: str = "legacy.domain.utils.intel",
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
        # 1) extrai a data do quarter (string -> datetime) e o mês do quarter
        def qdate_of(r: StatementRawDTO) -> datetime | None:
            # aceita "YYYY-MM[-DD]" ou "DD/MM/YYYY"; idealmente delegar ao DataCleaner
            txt = getattr(r, "quarter", None)
            if not txt:
                return None
            for fmt in ("%Y-%m-%d", "%Y-%m", "%d/%m/%Y"):
                try:
                    return datetime.strptime(str(txt), fmt)
                except ValueError:
                    pass
            return None

        # 2) agrupa por (company, ano, conta) e indexa por mês do quarter {3,6,9,12}
        groups: dict[tuple[str | None, int, str], dict[int, StatementRawDTO]] = {}
        for r in raws:
            d = qdate_of(r)
            if not d:
                # sem data válida: trata como cópia direta
                key = (r.company_name, 0, self._account_of(r))
                groups.setdefault(key, {})[0] = r
                continue
            ym = (d.year, d.month)
            key = (r.company_name, ym[0], self._account_of(r))
            groups.setdefault(key, {})[ym[1]] = r  # meses 3,6,9,12

        # 3) aplica regras preservando ordem dos meses
        for (_, _, account), mmap in groups.items():
            family = (account or "")[:1]
            # remapeia para índices "quarto" por mês
            qmap: dict[int, StatementRawDTO] = {}
            for m, row in mmap.items():
                qidx = {3: 1, 6: 2, 9: 3, 12: 4}.get(m, 0)
                qmap[qidx] = row
            if family in {"6", "7"}:
                yield from self._diff_quarters(qmap)
            elif family in {"3", "4"}:
                yield from self._adjust_q4(qmap)
            else:
                yield from self._copy(qmap)

    @staticmethod
    def _default_builder(raw: StatementRawDTO, target_line: str, value: Decimal) -> StatementFetchedDTO:
        # quarter como texto YYYY-MM (mês do quarter)
        qtxt = getattr(raw, "quarter", None)
        q_out = None
        if qtxt:
            for fmt in ("%Y-%m-%d", "%Y-%m", "%d/%m/%Y"):
                try:
                    d = datetime.strptime(str(qtxt), fmt)
                    q_out = f"{d.year:04d}-{d.month:02d}"
                    break
                except ValueError:
                    continue

        ver = getattr(raw, "version", None)
        ver_str = str(ver) if ver is not None else None

        return StatementFetchedDTO(
            id=None,
            nsd=str(getattr(raw, "nsd", "")),
            company_name=getattr(raw, "company_name", None),
            quarter=q_out,  # data normalizada YYYY-MM
            version=ver_str,
            grupo=str(getattr(raw, "grupo", "")),
            quadro=str(getattr(raw, "quadro", "")),
            account=str(getattr(raw, "account", getattr(raw, "account_code", ""))),
            description=str(getattr(raw, "description", "")),
            value=float(value),
            processing_hash="",
        )

    def _diff_quarters(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
        q1 = qmap.get(1); q2 = qmap.get(2); q3 = qmap.get(3); q4 = qmap.get(4)
        if q1: yield self._with_value(q1, self._dec(q1.value))
        if q2:
            base = self._dec(q1.value) if q1 else Decimal(0)
            yield self._with_value(q2, self._dec(q2.value) - base)
        if q3:
            base = self._dec(q2.value) if q2 else (self._dec(q1.value) if q1 else Decimal(0))
            yield self._with_value(q3, self._dec(q3.value) - base)
        if q4:
            base = self._dec(q3.value) if q3 else (self._dec(q2.value) if q2 else (self._dec(q1.value) if q1 else Decimal(0)))
            yield self._with_value(q4, self._dec(q4.value) - base)

    def _adjust_q4(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
        q1 = qmap.get(1); q2 = qmap.get(2); q3 = qmap.get(3); q4 = qmap.get(4)
        if q1: yield self._with_value(q1, self._dec(q1.value))
        if q2: yield self._with_value(q2, self._dec(q2.value))
        if q3: yield self._with_value(q3, self._dec(q3.value))
        if q4:
            soma = Decimal(0)
            if q1: soma += self._dec(q1.value)
            if q2: soma += self._dec(q2.value)
            if q3: soma += self._dec(q3.value)
            yield self._with_value(q4, self._dec(q4.value) - soma)

    def _copy(self, qmap: Dict[int, StatementRawDTO]) -> Iterable[StatementRawDTO]:
        for q in sorted(qmap):
            r = qmap[q]
            yield self._with_value(r, self._dec(r.value))

    # ---------- 2) 'Intel': classifica e gera FETCHED ----------
    def _classify_with_intel(self, rows: Sequence[StatementRawDTO]) -> List[StatementFetchedDTO]:
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

                if cond == "equals" and v_cmp != n_cmp: return False
                if cond == "not_equals" and v_cmp == n_cmp: return False
                if cond == "startswith" and not v_cmp.startswith(n_cmp): return False
                if cond == "contains_any" and not any(tok in value for tok in bag): return False
                if cond in ("contains_all",) and not all(tok in value for tok in bag): return False
                if cond in ("not_contains", "contains_none") and any(tok in value for tok in bag): return False
                if cond == "level":
                    level = value.count(".") + 1 if value else 1
                    try:
                        expected = int(needle)
                    except Exception:
                        return False
                    if level != expected: return False
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
            fetched = [self._build_fetched(r, node["target_line"], self._dec(getattr(r, "value", 0))) for r in hits]
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

    # ---------- utilitários ----------
    @staticmethod
    def _dec(x) -> Decimal:
        return x if isinstance(x, Decimal) else Decimal(str(x))

    @staticmethod
    def _with_value(raw: StatementRawDTO, value: Decimal) -> StatementRawDTO:
        if is_dataclass(raw):
            return replace(raw, value=value)
        raise TypeError("StatementRawDTO precisa ser dataclass para clonar com novo valor.")

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
