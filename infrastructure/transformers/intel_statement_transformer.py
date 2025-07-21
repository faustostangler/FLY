"""Financial intelligence adapter implementing legacy parsing logic."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

# =======
# # =======
# # """Financial intelligence adapter that calculates simple ratios."""
# # from __future__ import annotations
# # from typing import Dict, List, Tuple
# # >>>>>>> 2025-07-16-Statements-Round-2
# >>>>>>> 2025-07-16-Statements-Round-2
from application.ports import StatementTransformerPort
from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.utils import parse_quarter
from infrastructure.config import Config


class IntelStatementTransformerAdapter(StatementTransformerPort):
    """Apply business rules to parsed statements."""

    def __init__(self, config: Config) -> None:
        self.section_criteria = config.transformers.intel_section_criteria
        self.year_end_prefixes = config.transformers.intel_year_end_prefixes
        self.cumulative_prefixes = config.transformers.intel_cumulative_prefixes

    def transform(self, rows: List[RawStatementDTO]) -> List[ParsedStatementDTO]:
        """Run the Intel transformation pipeline."""
        filtered = self._filter_newer_versions(rows)
        standardized = self.generate_standard_financial_statements(filtered)
        cleaned = self.adjust_columns(standardized)
        corrected = self.detect_and_correct_outliers(cleaned)
        adjusted = self._transform_quarterly_values(corrected)
        return adjusted

    # Filtering -------------------------------------------------------------
    def _filter_newer_versions(
        self, rows: Iterable[RawStatementDTO]
    ) -> List[ParsedStatementDTO]:
        latest: Dict[
            Tuple[str | None, str | None, str | None, str | None, str],
            ParsedStatementDTO,
        ] = {}
        for row in rows:
            key = (row.company_name, row.quarter, row.grupo, row.quadro, row.account)
            version = self._version_int(row.version)
            existing = latest.get(key)
            if not existing or version > self._version_int(existing.version):
                latest[key] = ParsedStatementDTO(**row.__dict__)
        return list(latest.values())

    def _version_int(self, version: str | None) -> int:
        try:
            if not version:
                return 0
            digits = ''.join(filter(str.isdigit, version))
            return int(digits) if digits else 0
        except ValueError:
            return 0

    # Standardization ------------------------------------------------------
    def generate_standard_financial_statements(
        self, rows: Iterable[ParsedStatementDTO]
    ) -> List[ParsedStatementDTO]:
        result: List[ParsedStatementDTO] = []
        for row in rows:
            data = row.__dict__.copy()
            for _name, criteria in self.section_criteria:
                for item in criteria:
                    data = self.apply_criteria(data, item)
            result.append(ParsedStatementDTO(**data))
        return result

    def apply_criteria(self, data: Dict, criteria_item: dict) -> Dict:
        if self._matches(data, criteria_item.get("criteria", [])):
            target = criteria_item.get("target_line", "")
            if " - " in target:
                account, desc = target.split(" - ", 1)
                data["account"] = account
                data["description"] = desc
            for sub in criteria_item.get("sub_criteria", []):
                data = self.apply_criteria(data, sub)
        return data

    def _matches(self, data: Dict, filters: Iterable[Tuple[str, str, object]]) -> bool:
        for col, cond, val in filters:
            value = str(data.get(col, "") or "").lower()
            if cond == "equals" and value != str(val).lower():
                return False
            if cond == "not_equals" and value == str(val).lower():
                return False
            if cond == "startswith" and not value.startswith(str(val).lower()):
                return False
            if cond == "contains_any":
                vals = val if isinstance(val, list) else [val]
                if not any(re.search(re.escape(str(v).lower()), value) for v in vals):
                    return False
            if cond == "contains_all":
                vals = val if isinstance(val, list) else [val]
                if not all(re.search(re.escape(str(v).lower()), value) for v in vals):
                    return False
            if cond in ("not_contains", "contains_none"):
                vals = val if isinstance(val, list) else [val]
                if any(re.search(re.escape(str(v).lower()), value) for v in vals):
                    return False
            if cond == "level":
                level = value.count(".") + 1 if value else 1
                if level != int(val):
                    return False
        return True

    # Cleanup --------------------------------------------------------------
    def adjust_columns(
        self, rows: Iterable[ParsedStatementDTO]
    ) -> List[ParsedStatementDTO]:
        return [
            ParsedStatementDTO(
                **{
                    **row.__dict__,
                    "account": row.account.strip(),
                    "description": row.description.strip(),
                }
            )
            for row in rows
        ]

    # Outlier Detection ----------------------------------------------------
    def detect_and_correct_outliers(
        self, rows: Iterable[ParsedStatementDTO]
    ) -> List[ParsedStatementDTO]:
        groups: Dict[Tuple[str | None, str], List[ParsedStatementDTO]] = {}
        for row in rows:
            key = (row.company_name, row.account)
            groups.setdefault(key, []).append(row)

        results: List[ParsedStatementDTO] = []
        for items in groups.values():
            items.sort(key=lambda r: r.quarter or "")
            corrected: List[ParsedStatementDTO] = []
            for i, row in enumerate(items):
                prev_val = items[i - 1].value if i > 0 else None
                next_val = items[i + 1].value if i + 1 < len(items) else None
                new_val = row.value
                if prev_val and abs(prev_val * 1000 - row.value) < 1e-6:
                    new_val = prev_val
                if next_val and abs(next_val * 1000 - row.value) < 1e-6:
                    new_val = next_val
                data = {**row.__dict__, "value": new_val}
                corrected.append(ParsedStatementDTO(**data))
            results.extend(corrected)
        return results

    # Quarterly Transform --------------------------------------------------
    def _transform_quarterly_values(
        self, rows: Iterable[ParsedStatementDTO]
    ) -> List[ParsedStatementDTO]:
        groups: Dict[Tuple[str | None, str | None, str], List[ParsedStatementDTO]] = {}
        for row in rows:
            dt = parse_quarter(row.quarter)
            year = str(dt.year) if dt else "0"
            key = (row.company_name, row.account, year)
            groups.setdefault(key, []).append(row)

        results: List[ParsedStatementDTO] = []
        for key, items in groups.items():
            items.sort(
                key=lambda r: parse_quarter(r.quarter) or parse_quarter("1900-01-01")
            )
            account = key[1]
            if account.startswith(self.year_end_prefixes):
                results.extend(self._adjust_year_end(items))
            elif account.startswith(self.cumulative_prefixes):
                results.extend(self._adjust_cumulative(items))
            else:
                results.extend(items)
        return results

    def _adjust_year_end(
        self, items: List[ParsedStatementDTO]
    ) -> List[ParsedStatementDTO]:
        cumulative = 0.0
        result: List[ParsedStatementDTO] = []
        for row in items:
            dt = parse_quarter(row.quarter)
            if dt and dt.month == 12:
                val = row.value - cumulative
            else:
                val = row.value
                cumulative += row.value
            data = {**row.__dict__, "value": val}
            result.append(ParsedStatementDTO(**data))
        return result

    def _adjust_cumulative(
        self, items: List[ParsedStatementDTO]
    ) -> List[ParsedStatementDTO]:
        previous = 0.0
        result: List[ParsedStatementDTO] = []
        for row in items:
            val = row.value - previous
            previous = row.value
            data = {**row.__dict__, "value": val}
            result.append(ParsedStatementDTO(**data))
        return result


# =======
# # =======


# # class IntelStatementTransformerAdapter(StatementTransformerPort):
# #     """Add basic financial ratios to parsed statements."""

# #     def transform(self, rows: List[RawStatementDTO]) -> List[ParsedStatementDTO]:
# #         parsed = [
# #             row
# #             if isinstance(row, ParsedStatementDTO)
# #             else ParsedStatementDTO(**row.__dict__)
# #             for row in rows
# #         ]

# #         grouped: Dict[Tuple[str | None, str | None], List[ParsedStatementDTO]] = {}
# #         for row in parsed:
# #             key = (row.company_name, row.quarter)
# #             grouped.setdefault(key, []).append(row)

# #         results = list(parsed)
# #         for (company, quarter), items in grouped.items():
# #             assets = sum(r.value for r in items if r.account.startswith("01"))
# #             liabilities = sum(r.value for r in items if r.account.startswith("02"))
# #             ratio = liabilities / assets if assets else 0.0
# #             base = items[0]
# #             results.append(
# #                 ParsedStatementDTO(
# #                     nsd=base.nsd,
# #                     company_name=company,
# #                     quarter=quarter,
# #                     version=base.version,
# #                     grupo="INDICATORS",
# #                     quadro="RATIOS",
# #                     account="11.02",
# #                     description="Passivos por Ativos",
# #                     value=ratio,
# #                 )
# #             )
# #         return results
# # >>>>>>> 2025-07-16-Statements-Round-2
# >>>>>>> 2025-07-16-Statements-Round-2
