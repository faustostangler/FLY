"""Financial intelligence adapter implementing legacy parsing logic."""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, Iterable, List, Tuple

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
        ## tem que ver se é melhor primeiro filtrar os repitidos, depois stantard, depois comparar o hash por ano, depois calcular os anos onde houver diferença
        ## ou se manter como está agora
        from infrastructure.utils.csv_utils import save_dtos_to_csv
        save_dtos_to_csv(rows, "raws_statements_stage_4_1.csv")

        standardized = self.generate_standard_financial_statements(rows)
        from infrastructure.utils.csv_utils import save_dtos_to_csv
        save_dtos_to_csv(standardized, "raws_statements_stage_4_2_stantardized.csv")

        cleaned = self.adjust_columns(standardized)
        from infrastructure.utils.csv_utils import save_dtos_to_csv
        save_dtos_to_csv(cleaned, "raws_statements_stage_4_3_cleaned.csv")

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
        self, rows: Iterable[RawStatementDTO]
    ) -> List[ParsedStatementDTO]:
        """
        Transforma statements crus em statements padronizados conforme Intel.
        Somente inclui linhas que casam com os critérios definidos em intel.py.
        """
        result: List[ParsedStatementDTO] = []
        for row in rows:
            data = row.__dict__.copy()
            normalized_data = self._normalize_dict(data)

            # Percorre seções e critérios do Intel
            for account, item in self.section_criteria:
                # Caso 1: item é lista de dicionários
                if isinstance(item, list):
                    for sub_item in item:
                        matched_rows = self._apply_criteria_recursive(data, normalized_data, account, sub_item)
                        result.extend(matched_rows)
                # Caso 2: item é um único dicionário
                else:
                    matched_rows = self._apply_criteria_recursive(
                        data, normalized_data, account, item  # type: ignore
                    )
                    result.extend(matched_rows)
        return result

    def _normalize_dict(self, data: Dict) -> Dict:
        """
        Remove acentos, espaços extras e baixa para lowercase.
        Igual ao comportamento do legacy.
        """
        normalized = {}
        for k, v in data.items():
            text = str(v or "").lower()
            text = unicodedata.normalize("NFD", text)
            text = "".join(c for c in text if unicodedata.category(c) != "Mn")
            text = re.sub(r"\s+", " ", text.strip())
            normalized[k] = text
        return normalized

    def _apply_criteria_recursive(
        self,
        original_data: Dict,
        normalized_data: Dict,
        account: str,
        item: Dict
    ) -> List[ParsedStatementDTO]:
        """
        Aplica critério principal e sub-critérios de forma recursiva.
        Retorna uma lista de ParsedStatementDTO gerados.
        """
        generated: List[ParsedStatementDTO] = []

        # Se não casou, retorna lista vazia
        if not self._matches(normalized_data, item.get("criteria", [])):
            return generated

        # Cria linha base
        base_data = original_data.copy()
        base_account = base_data.get("account", "")
        base_description = base_data.get("description", "")

        target_line = item.get("target_line")
        if target_line:
            parts = target_line.split(" - ", 1)
            base_data["account"] = parts[0].strip()
            base_data["description"] = parts[1].strip() if len(parts) > 1 else base_description
        else:
            # fallback para não quebrar
            base_data["account"] = base_account
            base_data["description"] = base_description

        # para que os subníveis vejam as alterações
        new_normalized = self._normalize_dict(base_data)

        # Cria DTO para este nível
        generated.append(ParsedStatementDTO(**base_data))

        # Para cada subcritério, gera novas linhas
        for sub in item.get("sub_criteria", []):
            sub_level_data = base_data.copy()
            generated.extend(self._apply_criteria_recursive(sub_level_data, new_normalized, account, sub))

        return generated

    def apply_criteria(self, data: Dict, item: dict) -> Dict:
        if self._matches(data, item.get("criteria", [])):
            target = item.get("target_line", "")
            if " - " in target:
                account, desc = target.split(" - ", 1)
                data["account"] = account
                data["description"] = desc
            for sub in item.get("sub_criteria", []):
                data = self.apply_criteria(data, sub)
        return data

    def _matches(self, data: Dict, criteriae: Iterable[tuple[str, str, str | int | list[str | int]]]) -> bool:
        """
        Retorna True somente se TODOS os critérios forem atendidos.
        """
        for column, condition, account in criteriae:
            value = str(data.get(column, "") or "").lower()

            # string treatment
            if condition == "equals" and value != str(account).lower():
                return False
            if condition == "not_equals" and value == str(account).lower():
                return False
            if condition == "startswith" and not value.startswith(str(account).lower()):
                return False

            # list treatments
            accounts = account if isinstance(account, list) else [account]
            if condition == "contains_any":
                if not any(re.search(re.escape(str(v).lower()), value) for v in accounts):
                    return False
            if condition == "contains_all":
                if not all(re.search(re.escape(str(v).lower()), value) for v in accounts):
                    return False
            if condition in ("not_contains", "contains_none"):
                if any(re.search(re.escape(str(v).lower()), value) for v in accounts):
                    return False

            # level treatment
            if condition == "level":
                level = value.count(".") + 1 if value else 1
                if isinstance(account, (list, tuple)):
                    return False
                try:
                    expected_level = int(account)
                except (ValueError, TypeError):
                    return False
                if level != expected_level:
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

