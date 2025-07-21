from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

from application.ports import StatementTransformerPort
from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from infrastructure.config import Config


class MathStatementTransformerAdapter(StatementTransformerPort):
    """Adjust quarterly statement values."""

    def __init__(self, config: Config) -> None:
        self.year_end_prefixes = tuple(config.transformers.math_year_end_prefixes)
        self.cumulative_prefixes = tuple(config.transformers.math_cumulative_prefixes)

    def _group_key(self, row: RawStatementDTO, dt: datetime | None) -> Tuple:
        year = dt.year if dt else 0
        return (
            row.company_name or "",
            row.account,
            row.grupo,
            row.quadro,
            str(year),
            row.version or "",
        )
    def _parse(self, quarter: str | None) -> datetime | None:
        if not quarter:
            return None
        try:
            return datetime.fromisoformat(quarter)
        except ValueError:
            return None

    def transform(self, rows: List[RawStatementDTO]) -> List[ParsedStatementDTO]:
        groups: Dict[
            Tuple[str, str, str, str, str, str], List[Tuple[datetime | None, RawStatementDTO]]
        ] = {}
        for row in rows:
            dt = self._parse(row.quarter)
            key = self._group_key(row, dt)
            groups.setdefault(key, []).append((dt, row))

        result: List[ParsedStatementDTO] = []
        for key, items in groups.items():
            if len(items)>4:
                print(f"Grupo de tamanho maior que 4 itens, possíveis duplicatas\n{items}")

            items.sort(key=lambda x: (x[0] or datetime.min))
            account = key[1]
            if account.startswith(self.year_end_prefixes):
                result.extend(self._adjust_year_end(items))
            elif account.startswith(self.cumulative_prefixes):
                result.extend(self._adjust_cumulative(items))
            else:
                result.extend(self._as_parsed(items))
        return result

    def _as_parsed(
        self, items: List[Tuple[datetime | None, RawStatementDTO]]
    ) -> List[ParsedStatementDTO]:
        return [
            ParsedStatementDTO(
                nsd=row.nsd,
                company_name=row.company_name,
                quarter=row.quarter,
                version=row.version,
                grupo=row.grupo,
                quadro=row.quadro,
                account=row.account,
                description=row.description,
                value=row.value,
                processing_hash="",
            )
            for _dt, row in items
        ]

    def _adjust_year_end(
        self, items: List[Tuple[datetime | None, RawStatementDTO]]
    ) -> List[ParsedStatementDTO]:
        values: List[ParsedStatementDTO] = []
        cumulative = 0.0
        for dt, row in items:
            if dt and dt.month == 12:
                val = row.value - cumulative
            else:
                val = row.value
                cumulative += row.value
            values.append(
                ParsedStatementDTO(
                    nsd=row.nsd,
                    company_name=row.company_name,
                    quarter=row.quarter,
                    version=row.version,
                    grupo=row.grupo,
                    quadro=row.quadro,
                    account=row.account,
                    description=row.description,
                    value=val,
                    processing_hash="",
                )
            )
        return values

    def _adjust_cumulative(
        self, items: List[Tuple[datetime | None, RawStatementDTO]]
    ) -> List[ParsedStatementDTO]:
        values: List[ParsedStatementDTO] = []
        last = 0.0
        for dt, row in items:
            val = row.value - last
            last = row.value
            values.append(
                ParsedStatementDTO(
                    nsd=row.nsd,
                    company_name=row.company_name,
                    quarter=row.quarter,
                    version=row.version,
                    grupo=row.grupo,
                    quadro=row.quadro,
                    account=row.account,
                    description=row.description,
                    value=val,
                    processing_hash="",
                )
            )
        return values
