# application/processors/filter_builder.py
from __future__ import annotations
from typing import Any
from dataclasses import dataclass
from domain.utils.specs import And, Or, Not, Cmp, StrMatch, NullCheck, ListAny, Spec

@dataclass(frozen=True)
class FilterBuilder:
    '''
    Exemplo de estrutura de árvore aceita::

        {
            "and": [
                {"status": "ATIVO"},
                {
                    "or": [
                        {"has_bdr": True},
                        {"market": {"in": ["NM"]}},
                    ]
                },
                {"listing_date": {">=": "2020-01-01"}},
            ]
        }

    Operadores aceitos pelo FilterBuilder (um por linha):

    # Lógicos (estrutura da árvore)
    and → todas as condições verdadeiras.
    or → pelo menos uma condição verdadeira.
    not → inverte o resultado do filtro interno.

    # Comparativos numéricos ou de data (folhas Cmp)
    == ou eq → igual a.
    != ou ne → diferente de.
    >  ou gt → maior que.
    >= ou gte → maior ou igual a.
    <  ou lt → menor que.
    <= ou lte → menor ou igual a.
    in → valor está dentro de uma lista.
    nin → valor não está dentro de uma lista.
    between → valor entre dois limites (inclusive).

    # Textuais (folhas StrMatch)
    contains → texto contém o padrão.
    startswith → texto começa com o padrão.
    endswith → texto termina com o padrão.
    regex → casa com expressão regular.
    modificadores opcionais: case (sensível a maiúsculas), na (como tratar nulos).
    
    # Listas ou colunas JSON (folhas ListAny)
    contains → elemento exato existe na lista.
    in → algum item da lista pertence ao conjunto informado.
    overlap → há interseção entre listas.
    
    # Nulos (folhas NullCheck)
    valor None → é nulo (isnull).
    valor "isnull" → é nulo.
    valor "notnull" → não é nulo.
    '''

    # aceita nomes e símbolos
    _cmp_map = {
        "eq": "==", "==": "==",
        "ne": "!=", "!=": "!=",
        "gt": ">",  ">":  ">",
        "gte": ">=",">=": ">=",
        "lt": "<",  "<":  "<",
        "lte": "<=","<=": "<=",
        "in": "in",
        "nin": "nin",
        "between": "between",
    }
    _str_modes = {"contains", "startswith", "endswith", "regex"}
    _list_ops = {"contains", "in", "overlap"}

    @staticmethod
    def build_spec(d: Any) -> Spec:
        # nós lógicos
        if isinstance(d, dict) and set(d.keys()) == {"and"}:
            return And(tuple(FilterBuilder.build_spec(x) for x in d["and"]))
        if isinstance(d, dict) and set(d.keys()) == {"or"}:
            return Or(tuple(FilterBuilder.build_spec(x) for x in d["or"]))
        if isinstance(d, dict) and set(d.keys()) == {"not"}:
            return Not(FilterBuilder.build_spec(d["not"]))

        # folha: {"campo": condicao}
        if isinstance(d, dict) and len(d) == 1:
            field, cond = next(iter(d.items()))

            # null checks
            if cond is None:
                return NullCheck(field, negate=False)
            if isinstance(cond, str) and cond.lower() in ("isnull", "notnull"):
                return NullCheck(field, negate=(cond.lower() == "notnull"))

            # string matching, com suporte a contains + regex flag
            if isinstance(cond, dict) and any(k in cond for k in FilterBuilder._str_modes):
                # se pediu contains + regex=True, trate como regex
                if "contains" in cond and cond.get("regex", False) is True:
                    return StrMatch(
                        field=field, mode="regex", pattern=str(cond["contains"]),
                        case=cond.get("case", True), na=cond.get("na", False)
                    )
                # modos diretos
                for k in ("regex", "contains", "startswith", "endswith"):
                    if k in cond:
                        return StrMatch(
                            field=field, mode=k, pattern=str(cond[k]),
                            case=cond.get("case", True), na=cond.get("na", False)
                        )

            # colunas lista/JSON
            if isinstance(cond, dict) and any(k in cond for k in FilterBuilder._list_ops):
                for k in ("contains", "in", "overlap"):
                    if k in cond:
                        return ListAny(field=field, op=k, value=cond[k])

            # comparativos: aceita nomes e símbolos
            if isinstance(cond, dict):
                # garanta que só haja um operador por dict; se houver mais, o primeiro vence
                for k, sym in FilterBuilder._cmp_map.items():
                    if k in cond:
                        return Cmp(field=field, op=sym, value=cond[k])

            # igualdade direta: {"campo": valor}
            return Cmp(field=field, op="==", value=cond)

        # lista na raiz vira OR implícito
        if isinstance(d, list):
            return Or(tuple(FilterBuilder.build_spec(x) for x in d))

        raise ValueError(f"Filtro inválido: {d}")
