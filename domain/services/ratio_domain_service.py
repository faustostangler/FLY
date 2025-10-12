from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from typing import Dict, List, Mapping, Sequence, Set, Tuple

import numpy as np

from application.ports.logger_port import LoggerPort
from domain.dtos.normalized_series_dto import NormalizedSeriesBundleDTO
from domain.dtos.ratio_result_dto import RatioResultDTO


_METRIC_TOKEN = re.compile(r"^(?P<code>[^()]+?)(?:\((?P<offset>[-+]?\d+)\))?$")


@dataclass(frozen=True)
class _FormulaDefinition:
    account: str
    description: str
    formula: object
    dependencies: Tuple[str, ...]


class _DailyFrame:
    def __init__(self, bundle: NormalizedSeriesBundleDTO) -> None:
        self._bundle = bundle
        self._calendar = bundle.calendar
        self._company = bundle.company_id

    def __len__(self) -> int:
        return len(self._calendar)

    @property
    def index(self) -> List[Tuple[str, datetime]]:
        return [(self._company, day) for day in self._calendar]

    def __getitem__(self, key: str) -> np.ndarray:
        code, offset = _parse_metric_token(key)
        series = self._bundle.get(code)
        size = len(self._calendar)
        if series is None:
            return np.full(size, np.nan)

        base_array = np.array(
            [np.nan if value is None else float(value) for value in series.values],
            dtype=float,
        )
        if offset == 0:
            return base_array
        return _shift_array(base_array, offset)


def _parse_metric_token(token: str) -> Tuple[str, int]:
    match = _METRIC_TOKEN.match(token.strip())
    if match is None:
        return token, 0
    code = match.group("code")
    offset_raw = match.group("offset")
    offset = int(offset_raw) if offset_raw is not None else 0
    return code, offset


def _shift_array(array: np.ndarray, offset: int) -> np.ndarray:
    result = np.full_like(array, np.nan)
    if offset == 0:
        return array
    size = len(array)
    for idx in range(size):
        src = idx - offset
        if 0 <= src < size:
            result[idx] = array[src]
    return result


def _extract_dependencies(obj: object) -> Set[str]:
    if isinstance(obj, str):
        return {obj}
    if isinstance(obj, (int, float)):
        return set()
    deps: Set[str] = set()
    if isinstance(obj, (list, tuple)):
        for item in obj:
            deps.update(_extract_dependencies(item))
        return deps
    for value in vars(obj).values():
        deps.update(_extract_dependencies(value))
    return deps


class RatioDomainService:
    """Evaluate ratio formulas over normalized daily series."""

    def __init__(
        self,
        *,
        intel_module_path: str | None = None,
        logger: LoggerPort | None = None,
    ) -> None:
        module_path = intel_module_path or "domain.utils.intel"
        self._module = import_module(module_path)
        self._logger = logger
        self._definitions = self._load_definitions()

    def _load_definitions(self) -> Tuple[_FormulaDefinition, ...]:
        definitions: List[_FormulaDefinition] = []
        for name in dir(self._module):
            if not name.startswith("ratios_"):
                continue
            value = getattr(self._module, name, None)
            if not isinstance(value, list):
                continue
            for entry in value:
                account = str(entry.get("account"))
                description = str(entry.get("description", ""))
                formula = entry.get("formula")
                dependencies = tuple(sorted(_extract_dependencies(formula)))
                definitions.append(
                    _FormulaDefinition(
                        account=account,
                        description=description,
                        formula=formula,
                        dependencies=dependencies,
                    )
                )
        return tuple(definitions)

    def calculate(self, bundle: NormalizedSeriesBundleDTO) -> Sequence[RatioResultDTO]:
        if len(bundle.calendar) == 0:
            return []
        frame = _DailyFrame(bundle)
        results: List[RatioResultDTO] = []

        for definition in self._definitions:
            try:
                values = definition.formula(frame)
            except KeyError as exc:
                if self._logger is not None:
                    self._logger.log(
                        f"Missing metric {exc} for ratio {definition.account}",
                        level="warning",
                    )
                continue

            if not isinstance(values, np.ndarray):
                values = np.array(values, dtype=float)

            for idx, (company_id, day) in enumerate(frame.index):
                versions_map: Dict[str, str | None] = {}
                hashes_map: Dict[str, str | None] = {}
                missing: List[str] = []

                for token in definition.dependencies:
                    code, offset = _parse_metric_token(token)
                    series = bundle.get(code)
                    if series is None:
                        versions_map[token] = None
                        hashes_map[token] = None
                        missing.append(token)
                        continue
                    target = idx + offset
                    if target < 0 or target >= len(series.values):
                        versions_map[token] = None
                        hashes_map[token] = None
                        missing.append(token)
                        continue
                    value = series.values[target]
                    versions_map[token] = series.versions[target]
                    hashes_map[token] = series.hashes[target]
                    if value is None:
                        missing.append(token)

                ratio_value: float | None
                raw_value = values[idx]
                if missing:
                    ratio_value = None
                    self._log_gap(definition.account, company_id, day, missing)
                else:
                    ratio_value = None if (raw_value is None or math.isnan(raw_value)) else float(raw_value)

                version_token = self._compute_version(definition.account, versions_map)
                hash_token = self._compute_hash(definition.account, hashes_map, ratio_value)

                results.append(
                    RatioResultDTO(
                        company_id=company_id,
                        ratio_code=definition.account,
                        date=day,
                        value=ratio_value,
                        version=version_token,
                        calculation_hash=hash_token,
                        input_versions=RatioResultDTO.serialize_mapping(versions_map),
                        input_hashes=RatioResultDTO.serialize_mapping(hashes_map),
                        is_current=True,
                    )
                )

        return results

    def _log_gap(
        self,
        ratio_code: str,
        company_id: str,
        day: datetime,
        missing: Sequence[str],
    ) -> None:
        if self._logger is None:
            return
        missing_tokens = ", ".join(sorted(missing))
        self._logger.log(
            f"Missing inputs for ratio {ratio_code} company={company_id} date={day.date()}: {missing_tokens}",
            level="warning",
        )

    @staticmethod
    def _compute_version(
        ratio_code: str,
        versions: Mapping[str, str | None],
    ) -> str:
        ordered = sorted((key, value or "") for key, value in versions.items())
        payload = "|".join(f"{key}:{value}" for key, value in ordered)
        digest = hashlib.sha256(f"{ratio_code}|{payload}".encode("utf-8")).hexdigest()
        return digest

    @staticmethod
    def _compute_hash(
        ratio_code: str,
        hashes: Mapping[str, str | None],
        value: float | None,
    ) -> str:
        ordered = sorted((key, value or "") for key, value in hashes.items())
        value_token = "" if value is None else f"{value:.12g}"
        payload = "|".join(f"{key}:{val}" for key, val in ordered)
        digest = hashlib.sha256(
            f"{ratio_code}|{payload}|{value_token}".encode("utf-8")
        ).hexdigest()
        return digest
