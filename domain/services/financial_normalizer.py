# domain/services/financial_normalizer.py
from __future__ import annotations

from dataclasses import is_dataclass, replace
from datetime import datetime
# from decimal import Decimal
from typing import Any, Callable, Dict, Iterable, List, Tuple, Optional, Sequence

from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.statement_raw_dto import StatementRawDTO


class FinancialNormalizerPort:
    """Serviço puro de domínio: recebe RAW (ano, companhia) já deduplicado por versão,
    aplica a matemática de quarter e depois o 'intel' do legado, emitindo FETCHED."""
    def quarterize(self, raws: Sequence[StatementRawDTO]) -> Dict[tuple[str | None, datetime], List[StatementRawDTO]]:
        raise NotImplementedError
    def standardize(self, groups: Dict[tuple[str | None, datetime], List[StatementRawDTO]]) -> Sequence[StatementFetchedDTO]:
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
        self._intel_module_path = intel_module_path

    def quarterize(self, raws: Sequence[StatementRawDTO]) -> Dict[tuple[str | None, datetime], List[StatementRawDTO]]:
        # 1) matemática de quarter por conta no conjunto anual já deduplicado
        quarterized = list(self._apply_quarter_math(raws))

        # 2) agrupa por (company, quarter) e padroniza cada trimestre separadamente
        groups: Dict[tuple[str | None, datetime], List[StatementRawDTO]] = {}
        for r in quarterized:
            key = (getattr(r, "company_name", None), getattr(r, "quarter"))
            groups.setdefault(key, []).append(r)

        return groups

    def standardize(
        self,
        groups: Dict[Tuple[Optional[str], Any], List[StatementRawDTO]],
    ) -> Sequence[StatementFetchedDTO]:
        out: List[StatementFetchedDTO] = []
        norm_items: List[Tuple[str, datetime, List[StatementRawDTO]]] = []

        # aplica o intel por quarter, com diagnóstico local
        for (company, quarter), rows in groups.items():
            try:
                fetched_q = self._classify_with_intel(rows)
                out.extend(fetched_q)
            except Exception as e:
                raise RuntimeError(
                    f"Erro no intel para empresa={company} quarter={quarter.date()} linhas={len(rows)}"
                ) from e

        return out



    # ---------- 1) Matemática de quarter sobre RAW do ano deduplicado ----------
    # Caminho ATUAL: usa DATA do quarter; identifica pelo mês (03, 06, 09, 12) e converte acumulados conforme regras.
    def _apply_quarter_math(self, raws: Sequence[StatementRawDTO]) -> Iterable[StatementRawDTO]:
        # agrupa por (company, ano, quadro, grupo, account) e indexa por mês do quarter {3,6,9,12}
        groups: dict[tuple[str, int, str, str, str], dict[int, StatementRawDTO]] = {}
        for r in raws:
            q: datetime = r.quarter
            if hasattr(q, "year"):
                y, m = q.year, q.month
            else:
                y, m, *_ = str(q).split("-") + ["0", "0"]
                y, m = int(y), int(m)

            company_name = str(getattr(r, "company_name", "") or "")
            quadro = str(getattr(r, "quadro", "") or "")
            grupo = str(getattr(r, "grupo", "") or "")
            account = self._account_of(r)
            key = (company_name, y, quadro, grupo, account)
            groups.setdefault(key, {})[m] = r  # meses 3,6,9,12

        # 3) aplica regras preservando ordem dos meses
        for (company_name, year, quadro, grupo, account), mmap in groups.items():
            family = str(int(account.split(".")[0]))

            # qmap com meses reais como chaves (3, 6, 9, 12)
            qmap: dict[int, StatementRawDTO] = {int(m): row for m, row in mmap.items()}

            if family in {"6", "7"}:
                yield from self._diff_quarters(qmap)
            elif family in {"3", "4"}:
                yield from self._adjust_q4(qmap)
            else:
                yield from self._copy(qmap)

    @staticmethod
    # def _default_builder(raw: StatementRawDTO, column: str, value: Decimal) -> StatementFetchedDTO:
    def _default_builder(raw: StatementRawDTO, column: str) -> StatementFetchedDTO:
        # quarter como texto YYYY-MM (mês do quarter)
        account, sep, description = (column or "").partition(" - ")

        return StatementFetchedDTO(
            id=None,
            nsd=raw.nsd,
            company_name=raw.company_name,
            quarter=raw.quarter,
            version=raw.version,
            grupo=raw.grupo,
            quadro=raw.quadro,
            # quadro=raw.grupo,      # consolidação
            # grupo=raw.quadro,      # subquadro
            account=account,
            description=description,
            value=raw.value,
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
        """
        Aplica as regras de classificação ("intel") sobre um conjunto de RAW já
        ajustado por trimestre. Saída: StatementFetchedDTO por linha-alvo definida no intel.
        Fluxo:
        1) Carrega módulo intel configurado.
        2) Define utilitários para normalizar conta e comparar critérios.
        3) Constrói a árvore de critérios a partir do módulo intel.
        4) Percorre a árvore (walk): filtra hits, cria FETCHED e desce para subcritérios.
        """
        try:
            # 1) Carrega dinamicamente o módulo de regras "intel" (injetável por caminho).
            from importlib import import_module
            intel = import_module(self._intel_module_path)

            # ----- Utilitários locais -----

            def normalize_account(val: str) -> str:
                """
                Normaliza código de conta para formato canônico de comparação.
                - Remove zeros à esquerda em cada nível.
                - Repreenche com 2 dígitos por nível para comparação estável.
                Ex.: "01.1.002" -> "01.01.02"
                """
                parts = [(p.lstrip("0") or "0") for p in (val or "").split(".")]
                return ".".join(seg.zfill(2) for seg in parts)

            def account_of_raw(r: StatementRawDTO) -> str:
                """
                Obtém o código de conta do RAW aceitando variação de campo:
                - Usa 'account_code' se existir, senão 'account', senão vazio.
                """
                return getattr(r, "account_code", None) or getattr(r, "account", "") or ""

            def matches(row: StatementRawDTO, criteria: list[tuple[str, str, Any]]) -> bool:
                """
                Avalia se a linha 'row' satisfaz todos os pares (coluna, operador, valor) em 'criteria'.
                Operadores suportados:
                - equals, not_equals, startswith
                - contains_any, contains_all, not_contains|contains_none
                - level: compara profundidade do código de conta (nº de níveis)
                Regras especiais para 'account'/'account_code': comparam versão normalizada.
                """
                for column, condition, needle in criteria:
                    # Lê o valor bruto da coluna; para 'account', faz fallback para account_of_raw
                    raw_value = getattr(row, column, None)
                    if raw_value is None and column == "account":
                        raw_value = account_of_raw(row)
                    value = str(raw_value or "").lower()

                    # Normaliza conta quando o campo comparado é 'account' ou 'account_code'
                    if column in ("account", "account_code"):
                        v_cmp = normalize_account(value)
                        n_cmp = normalize_account(str(needle))
                    else:
                        v_cmp = value
                        n_cmp = str(needle).lower()

                    # Conjunto de termos para operadores baseados em inclusão
                    bag = needle if isinstance(needle, (list, tuple)) else [needle]
                    bag = [str(x).lower() for x in bag]

                    # Avaliação de cada operador
                    if condition == "equals":
                        if v_cmp != n_cmp:
                            return False
                    elif condition == "not_equals":
                        if v_cmp == n_cmp:
                            return False
                    elif condition == "startswith":
                        if not v_cmp.startswith(n_cmp):
                            return False
                    elif condition == "contains_any":
                        if not any(tok in value for tok in bag):
                            return False
                    elif condition in ("contains_all",):
                        if not all(tok in value for tok in bag):
                            return False
                    elif condition in ("not_contains", "contains_none"):
                        if any(tok in value for tok in bag):
                            return False
                    elif condition == "level":
                        # Profundidade: "1.02.03" => nível 3
                        level = value.count(".") + 1 if value else 1
                        needle_val = needle[0] if isinstance(needle, (list, tuple)) and needle else needle
                        try:
                            expected = needle_val  # tipicamente um int
                        except Exception:
                            return False
                        if level != expected:
                            return False

                return True  # Passou por todos os critérios

            def map_node(d: dict):
                """
                Converte um nó de regra do módulo intel para um dict interno padronizado:
                - column: nome da linha-alvo no FETCHED
                - criteria: lista de tuplas (coluna, operador, valor)
                - children: subcritérios a serem aplicados sobre o universo filtrado
                """
                return {
                    "column": d.get("column", ""),
                    "criteria": [tuple(c) for c in d.get("criteria", [])],
                    "children": [map_node(c) for c in d.get("sub_criteria", [])],
                }

            # 2) Coleta as raízes da árvore de critérios do módulo intel
            roots: list[dict] = []
            for name in dir(intel):
                if name.endswith("_criteria"):
                    value = getattr(intel, name)
                    if isinstance(value, list):
                        roots.extend(map(map_node, value))

            def walk(node: dict, universe: list[StatementRawDTO]) -> list[StatementFetchedDTO]:
                """
                Percorre um nó da árvore:
                a) Seleciona 'hits' no universo com base em 'criteria'.
                b) Para cada hit, cria um StatementFetchedDTO com a linha alvo e o valor numérico.
                c) Define conjunto de pais (accounts alvo) e chama recursivamente os filhos
                    com um universo restrito às contas descendentes desses pais.
                Retorna a lista de FETCHED criada neste nó e nos filhos.
                """
                try:
                    # a) Filtra as linhas do universo que casam com os critérios deste nó
                    hits = [r for r in universe if matches(r, node["criteria"])]

                    # b) Constrói FETCHED para cada hit usando o builder injetado
                    fetched: list[StatementFetchedDTO] = []
                    for row in hits:
                        fetched.append(self._default_builder(row, node["column"]))

                    parents = {normalize_account(getattr(fetched_row, "account", "")) for fetched_row in fetched}
                    if not parents:
                        return fetched

                    # Universo dos filhos: qualquer RAW cuja conta normalizada comece com algum pai
                    children_rows = [
                        r for r in universe
                        if any(normalize_account(account_of_raw(r)).startswith(p) for p in parents)
                    ]

                    # Para cada filho, concatena resultados recursivos
                    for child in node["children"]:
                        fetched.extend(walk(child, children_rows))
                    return fetched
                except Exception as e:
                    print(f"Erro no walk do nó {node}: {e}")
                    return []
            # 3) Executa a árvore inteira sobre as linhas do trimestre
            out: list[StatementFetchedDTO] = []
            for node in roots:
                out.extend(walk(node, list(rows)))  # copia defensiva do universo

            return out

        except Exception as e:
            # Em produção, prefira logger estruturado. Aqui mantemos fallback simples.
            print(e)

        # Falha defensiva: retorna lista vazia para não quebrar o pipeline upstream.
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
    # def _default_builder(raw: StatementRawDTO, column: str, value: Decimal) -> StatementFetchedDTO:
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
    #     )
