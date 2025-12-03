from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Sequence, Tuple

from domain.utils import intel

MATH_YEAR_END_PREFIXES: Tuple[str, ...] = ("3", "4")
MATH_CUMULATIVE_PREFIXES: Tuple[str, ...] = ("6", "7")
MATH_TARGET_ACCOUNTS: Tuple[str, ...] = (
    "00.01.01",
    "1",
    "2",
    "3.01",
    "4.01",
    "6.01",
    "7.01",
)
INTEL_YEAR_END_PREFIXES: Tuple[str, ...] = ("03", "04")
INTEL_CUMULATIVE_PREFIXES: Tuple[str, ...] = ("06", "07")

# Aqui garantimos Sequence[dict[str, object]] em tempo estático e valor imutável em tempo de execução
INTEL_SECTION_CRITERIA: Tuple[Tuple[str, Tuple[dict[str, object], ...]], ...] = (
    ("CAPITAL", tuple(intel.section_0_criteria)),
    ("BALANCE_ASSET", tuple(intel.section_1_criteria)),
    ("BALANCE_LIAB", tuple(intel.section_2_criteria)),
    ("INCOME", tuple(intel.section_3_criteria)),
    ("CASH_FLOW", tuple(intel.section_6_criteria)),
    ("VALUE_ADDED", tuple(intel.section_7_criteria)),
)


@dataclass(frozen=True)
class TransformersConfig:
    """Configuration for statement transformers."""

    _enabled: Mapping[str, bool] = field(
        default_factory=lambda: {"math": True, "intel": True}
    )
    _order: Tuple[str, ...] = field(default_factory=lambda: ("math", "intel"))
    math_year_end_prefixes: Tuple[str, ...] = field(
        default_factory=lambda: MATH_YEAR_END_PREFIXES
    )
    math_cumulative_prefixes: Tuple[str, ...] = field(
        default_factory=lambda: MATH_CUMULATIVE_PREFIXES
    )
    math_target_accounts: Tuple[str, ...] = field(
        default_factory=lambda: MATH_TARGET_ACCOUNTS
    )
    intel_year_end_prefixes: Tuple[str, ...] = field(
        default_factory=lambda: INTEL_YEAR_END_PREFIXES
    )
    intel_cumulative_prefixes: Tuple[str, ...] = field(
        default_factory=lambda: INTEL_CUMULATIVE_PREFIXES
    )
    intel_section_criteria: Tuple[
        Tuple[str, Tuple[dict[str, object], ...]],
        ...,
    ] = field(default_factory=lambda: INTEL_SECTION_CRITERIA)

    @property
    def enabled(self) -> Mapping[str, bool]:
        return MappingProxyType(dict(self._enabled))

    @property
    def order(self) -> Sequence[str]:
        return self._order


def load_transformers_config() -> TransformersConfig:
    """Load the transformers configuration."""
    return TransformersConfig(
        _enabled={"math": True, "intel": True},
        _order=("math", "intel"),
        math_year_end_prefixes=MATH_YEAR_END_PREFIXES,
        math_cumulative_prefixes=MATH_CUMULATIVE_PREFIXES,
        math_target_accounts=MATH_TARGET_ACCOUNTS,
        intel_year_end_prefixes=INTEL_YEAR_END_PREFIXES,
        intel_cumulative_prefixes=INTEL_CUMULATIVE_PREFIXES,
        intel_section_criteria=INTEL_SECTION_CRITERIA,
    )
