"""Helpers to load Intel classification criteria into ``CriteriaNode``
trees."""

from __future__ import annotations

from typing import Iterable, List, Tuple

from domain.utils import intel
from domain.utils.criteria_node import CriteriaNode

INTEL_SECTION_CRITERIA: Tuple[Tuple[str, Iterable[dict]], ...] = (
    ("CAPITAL", intel.section_0_criteria),
    ("BALANCE_ASSET", intel.section_1_criteria),
    ("BALANCE_LIAB", intel.section_2_criteria),
    ("INCOME", intel.section_3_criteria),
    ("CASH_FLOW", intel.section_6_criteria),
    ("VALUE_ADDED", intel.section_7_criteria),
)


def _map_item(item: dict) -> CriteriaNode:
    children = [_map_item(child) for child in item.get("sub_criteria", [])]
    criteria = [tuple(c) for c in item.get("criteria", [])]
    return CriteriaNode(
        target_line=item.get("target_line", ""),
        criteria=criteria,
        children=children,
    )


def load_intel_criteria_nodes() -> List[CriteriaNode]:
    """Return the Intel criteria as a list of ``CriteriaNode`` objects."""
    nodes: List[CriteriaNode] = []
    for _name, items in INTEL_SECTION_CRITERIA:
        for item in items:
            nodes.append(_map_item(item))
    return nodes
