"""Financial intelligence adapter implementing legacy parsing logic."""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from application.ports import StatementTransformerPort
from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.services import StatementClassificationService
from domain.utils import parse_quarter
from infrastructure.config import Config
from infrastructure.config.intel_criteria import load_intel_criteria_nodes


class IntelStatementTransformerAdapter(StatementTransformerPort):
    """Apply business rules to parsed statements."""

    def __init__(
        self,
        config: Config,
        classification_service: StatementClassificationService,
    ) -> None:
        self.classification_service = classification_service
        self.criteria_tree = load_intel_criteria_nodes()
        self.year_end_prefixes = config.transformers.intel_year_end_prefixes
        self.cumulative_prefixes = config.transformers.intel_cumulative_prefixes

    def transform(self, rows: List[RawStatementDTO]) -> List[ParsedStatementDTO]:
        """Run the Intel transformation pipeline."""
        from infrastructure.utils.csv_utils import save_dtos_to_csv

        save_dtos_to_csv(rows, "raws_statements_stage_4_1.csv")

        deduped = self._filter_newer_versions(rows)

        standardized = self.classification_service.classify(deduped, self.criteria_tree)
        save_dtos_to_csv(standardized, "raws_statements_stage_4_2_stantardized.csv")

        cleaned = self.adjust_columns(standardized)
        save_dtos_to_csv(cleaned, "raws_statements_stage_4_3_cleaned.csv")

        corrected = self.detect_and_correct_outliers(cleaned)
        adjusted = self._transform_quarterly_values(corrected)
        return adjusted

    # Filtering -------------------------------------------------------------
    def _filter_newer_versions(
        self, rows: Iterable[RawStatementDTO]
    ) -> List[RawStatementDTO]:
        latest: Dict[
            Tuple[str | None, str | None, str | None, str | None, str],
            RawStatementDTO,
        ] = {}
        for row in rows:
            key = (row.company_name, row.quarter, row.grupo, row.quadro, row.account)
            version = self._version_int(row.version)
            existing = latest.get(key)
            if not existing or version > self._version_int(existing.version):
                latest[key] = row
        return list(latest.values())

    def _version_int(self, version: str | None) -> int:
        try:
            if not version:
                return 0
            digits = "".join(filter(str.isdigit, version))
            return int(digits) if digits else 0
        except ValueError:
            return 0

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
