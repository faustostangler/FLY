# domain/services/ratios_calculator.py
from __future__ import annotations

from importlib import import_module
from collections import defaultdict

from typing import Any, Dict, Optional, Protocol, Sequence, Tuple, runtime_checkable
from datetime import datetime
import numpy as np

from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.statement_raw_dto import StatementRawDTO


@runtime_checkable
class RatiosCalculatorPort(Protocol):
    # def calculate(self, standards: Sequence[StatementRawDTO]) -> Sequence[StatementFetchedDTO]: 
    def calculate(self, standards: Sequence[StatementFetchedDTO]) -> Sequence[StatementFetchedDTO]:
        ...


def _norm_acc(a: str | None) -> str:
    parts = [(p.lstrip("0") or "0") for p in str(a or "").split(".")]
    return ".".join(seg.zfill(2) for seg in parts)


class _ColumnarFrame:
    """
    Estrutura mínima exigida pelas fórmulas do intel:
      - len(frame) -> nº de períodos
      - frame["01.02.03"] -> np.ndarray alinhado ao índice
      - frame.index -> lista de chaves (nsd, company_name, quarter)
    """
    __slots__ = ("_index", "_cols")

    def __init__(self, rows: Sequence[StatementFetchedDTO]) -> None:
        buckets: Dict[Tuple[str, str | None, datetime], Dict[str, float]] = {}
        
        for r in rows:
            key = (
                str(getattr(r, "nsd", "")),
                getattr(r, "company_name", None),
                r.quarter,
            )
            raw_acc = _norm_acc(str(getattr(r, "account", getattr(r, "account_code", "")) or ""))
            val = float(getattr(r, "value", 0.0) or 0.0)
            m = buckets.setdefault(key, {})
            # última ocorrência vence
            m[raw_acc] = val


        self._index = sorted(buckets.keys())
        all_accs = {a for mp in buckets.values() for a in mp.keys()}
        self._cols = {
            acc: np.array([buckets[idx].get(acc, 0.0) for idx in self._index], dtype=float)
            for acc in all_accs
        }

    def __len__(self) -> int:
        return len(self._index)

    def __getitem__(self, acc: str) -> np.ndarray:
        col = self._cols.get(acc)
        if col is not None:
            return col
        # conta ausente => vetor zero
        return np.zeros(len(self), dtype=float)

    @property
    def index(self):
        return self._index


class RatiosCalculator(RatiosCalculatorPort):
    """
    Serviço puro: DTO -> DTO. Sem I/O e sem pandas.
    Carrega indicadores do módulo intel e avalia as fórmulas sobre um frame colunar.
    """

    def __init__(self, intel_module_path: str | None):
        # Fallback seguro para o legado quando vier None ou string vazia
        path = intel_module_path or "domain.utils.intel"
        self._intel_module_path = str(path)

        mod = import_module(self._intel_module_path)

        # Coleta apenas listas cujo nome começa com 'indicators_'
        indicators: list[dict] = []
        for attr in list(vars(mod).keys()):
            name = str(attr)
            if name.startswith("indicators_"):
                value = getattr(mod, name, None)
                if isinstance(value, list):
                    indicators.extend(value)
        self._indicators: list[dict] = indicators

    # def calculate(self, standards: Sequence[StatementRawDTO]) -> Sequence[StatementFetchedDTO]:
    def calculate(self, standards: Sequence[StatementFetchedDTO]) -> Sequence[StatementFetchedDTO]:
        if not standards:
            return []

        head_list = ["00"]
        out: list[StatementFetchedDTO] = []

        # 1) particiona
        commons: dict[tuple[str, str | None, datetime, str], list[StatementFetchedDTO]] = defaultdict(list)
        uniques: dict[tuple[str, str | None, datetime, str], list[StatementFetchedDTO]] = defaultdict(list)

        for row in standards:
            if str(getattr(row, "quadro", "")).startswith("Indicadores"):
                continue
            head = str(getattr(row, "account", "")).split(".")[0]
            key = (row.nsd, row.company_name, row.quarter, row.grupo)
            (commons if head in head_list else uniques)[key].append(row)

        # 2) calcula por grupo com overlay dos "00.*" de todo o trimestre
        for (nsd, company, quarter, grupo), rows in uniques.items():
            base: list[StatementFetchedDTO] = []
            for (nsd2, company2, quarter2, grupo2), rows_c in commons.items():
                if nsd2 == nsd and company2 == company and quarter2 == quarter:
                    base.extend(rows_c)

            # dedup dos comuns por (account, description) para não inflar o frame
            seen: set[tuple[str, str]] = set()
            base_dedup: list[StatementFetchedDTO] = []
            for r in base:
                k = (str(getattr(r, "account", "")), str(getattr(r, "description", "")))
                if k in seen:
                    continue
                seen.add(k)
                base_dedup.append(r)

            combined = base_dedup + rows
            frame = _ColumnarFrame(combined)

            for indicador in self._indicators:
                account: str = indicador["account"]
                description: str = indicador.get("description", "")
                formula = indicador["formula"]

                try:
                    values = formula(frame)
                except KeyError:
                    values = np.full(len(frame), np.nan)

                if not isinstance(values, np.ndarray):
                    values = np.array(values, dtype=float)

                for (nsd_i, company_i, quarter_i), value in zip(frame.index, values):
                    v = float(value) if np.isfinite(value) else 0.0
                    head_i = str(account).split(".")[0]           # "06.01" -> "06"

                    out.append(
                        StatementFetchedDTO(
                            id=None,
                            nsd=str(nsd_i),
                            company_name=company_i,
                            quarter=quarter_i,
                            version=None,
                            grupo=grupo,
                            quadro=f"Indicadores {head_i}",
                            account=account,
                            description=description,
                            value=v,
                            processing_hash="",
                        )
                    )

        return out
