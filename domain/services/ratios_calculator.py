# domain/services/ratios_calculator.py
from __future__ import annotations
from typing import Sequence, Dict, Tuple, Any, Protocol, runtime_checkable
from importlib import import_module
import numpy as np

from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.dtos.statement_fetched_dto import StatementFetchedDTO


@runtime_checkable
class RatiosCalculatorPort(Protocol):
    def calculate(self, standards: Sequence[StatementRawDTO]) -> Sequence[StatementFetchedDTO]: ...


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

    def __init__(self, rows: Sequence[StatementRawDTO]) -> None:
        buckets: Dict[Tuple[str, str | None, str], Dict[str, float]] = {}
        for r in rows:
            key = (
                str(getattr(r, "nsd", "")),
                getattr(r, "company_name", None),
                str(getattr(r, "quarter", None)),
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

    def calculate(self, standards: Sequence[StatementRawDTO]) -> Sequence[StatementFetchedDTO]:
        if not standards:
            return []

        frame = _ColumnarFrame(standards)
        out: list[StatementFetchedDTO] = []

        for ind in self._indicators:
            # cada item deve ter 'account', 'description' e 'formula' no intel.py
            acc_code: str = ind["account"]
            desc: str = ind.get("description", "")
            formula = ind["formula"]

            try:
                values = formula(frame)  # esperado: np.ndarray com len(frame)
            except KeyError:
                values = np.full(len(frame), np.nan)

            if not isinstance(values, np.ndarray):
                values = np.array(values, dtype=float)

            for (nsd, company_name, quarter), val in zip(frame.index, values):
                v = float(val) if np.isfinite(val) else 0.0
                out.append(
                    StatementFetchedDTO(
                        id=None,
                        nsd=str(nsd),
                        company_name=company_name,
                        quarter=quarter,
                        version=None,
                        grupo="Indicadores",
                        quadro="Intel",
                        account=acc_code,
                        description=desc,
                        value=v,
                        processing_hash="",
                    )
                )

        return out
