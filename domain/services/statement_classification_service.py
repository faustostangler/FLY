"""Service for classifying raw statements using criteria trees."""

from __future__ import annotations

from typing import Any, List, Tuple

from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.utils.criteria_node import CriteriaNode


class StatementClassificationService:
    """Apply criteria trees to raw statement rows."""

    def classify(
        self, rows: List[RawStatementDTO], roots: List[CriteriaNode]
    ) -> List[ParsedStatementDTO]:
        """Classify ``rows`` using ``roots`` criteria tree."""
        result: List[ParsedStatementDTO] = []
        for node in roots:
            # print(f"Processing node: {node.target_line}")
            result.extend(self._process_node(rows, node))
        return result

    def _process_node(
        self, rows: List[RawStatementDTO], node: CriteriaNode
    ) -> List[ParsedStatementDTO]:
        hits = [r for r in rows if self._matches(r, node.criteria)]
        parsed = [self._to_parsed(r, node.target_line) for r in hits]

        parents = {
            self._normalize_account(dto.account)
            for dto in parsed
        }
        if not parents:
            return parsed

        children_rows = [r for r in rows if any(self._normalize_account(r.account).startswith(p) for p in parents)]
        for child_node in node.children:
            parsed.extend(self._process_node(children_rows, child_node))
        return parsed

    def _to_parsed(self, row: RawStatementDTO, target_line: str) -> ParsedStatementDTO:
        parts = target_line.split(" - ", 1)
        account = parts[0].strip()
        # raw_account = parts[0].strip()
        # account = ".".join(seg.zfill(2) for seg in raw_account.split("."))
        description = parts[1].strip() if len(parts) > 1 else row.description
        return ParsedStatementDTO(
            nsd=row.nsd,
            company_name=row.company_name,
            quarter=row.quarter,
            version=row.version,
            grupo=row.grupo,
            quadro=row.quadro,
            account=account,
            description=description,
            value=row.value,
            processing_hash="",
        )

    def _format_account(self, acc: str) -> str:
        # primeiro normaliza (remove zeros à esquerda, trata vazios)
        parts = [(part.lstrip("0") or "0") for part in acc.split(".")]
        # depois preenche para ter sempre 2 dígitos
        return ".".join(part.zfill(2) for part in parts)

    def _matches(
        self, row: RawStatementDTO, criteria: List[Tuple[str, str, Any]]
    ) -> bool:
        for column, condition, account in criteria:
            value = str(getattr(row, column, "") or "").lower()

            if column == "account":
                value_cmp = self._normalize_account(value)
                account_cmp = self._normalize_account(str(account))
            else:
                value_cmp = value
                account_cmp = str(account).lower()

            if condition == "equals" and value_cmp != account_cmp:
                return False
            if condition == "not_equals" and value_cmp == account_cmp:
                return False
            if condition == "startswith" and not value_cmp.startswith(account_cmp):
                return False

            accounts = account if isinstance(account, list) else [account]
            if condition == "contains_any":
                if not any(str(v).lower() in value for v in accounts):
                    return False
            if condition == "contains_all":
                if not all(str(v).lower() in value for v in accounts):
                    return False
            if condition in ("not_contains", "contains_none"):
                if any(str(v).lower() in value for v in accounts):
                    return False

            if condition == "level":
                level = value.count(".") + 1 if value else 1
                if isinstance(account, (list, tuple)):
                    return False
                try:
                    expected = int(account)
                except (ValueError, TypeError):
                    return False
                if level != expected:
                    return False
        return True

    @staticmethod
    def _normalize_account(val: str) -> str:
        """Strip leading zeros de cada segmento e reconstrói o código."""
        return ".".join(part.lstrip("0") or "0" for part in val.split("."))
