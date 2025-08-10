from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Sequence, Tuple

from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.ports import ConfigPort, StatementTransformerPort


class MathStatementTransformerAdapter(StatementTransformerPort[ParsedStatementDTO, ParsedStatementDTO]):
    """Adjust quarterly statement values."""

    def __init__(self, config: ConfigPort) -> None:
        self.year_end_prefixes = tuple(config.transformers.math_year_end_prefixes)
        self.cumulative_prefixes = tuple(config.transformers.math_cumulative_prefixes)
        self.target_accounts = set(config.transformers.math_target_accounts)

    def _group_key(self, row: ParsedStatementDTO, dt: datetime | None) -> Tuple:
        year = dt.year if dt else 0
        return (
            row.company_name or "",
            row.account,
            row.grupo,
            row.quadro,
            str(year),
            "" # row.version or "",
        )

    def _parse(self, quarter: str | None) -> datetime | None:
        if not quarter:
            return None
        try:
            return datetime.fromisoformat(quarter)
        except ValueError:
            return None

    def transform(self, rows: Sequence[ParsedStatementDTO]) -> List[ParsedStatementDTO]:
        groups: Dict[
            Tuple[str, str, str, str, str, str],
            List[Tuple[datetime | None, ParsedStatementDTO]],
        ] = {}
        for row in rows:
            dt = self._parse(row.quarter)
            key = self._group_key(row, dt)
            groups.setdefault(key, []).append((dt, row))

        result: List[ParsedStatementDTO] = []
        for i, group in enumerate(groups.items()):
            (company, account, grupo, quadro, year, version), items = group

            if account in self.target_accounts:
                if len(items) > 4:
                    print(
                        f"Sheet {i}/{len(groups)} de tamanho maior que 4 itens, possíveis duplicatas\n{items}"
                    )
                elif len(items) == 1:
                    # print(
                    #     f"Sheet {i}/{len(groups)} de tamanho {len(items)}, único demonstrativo {items[0][1].quarter} {year} {version} - {grupo} {quadro} {account}"
                    # )
                    pass
                elif len(items) == 4:
                    # print(
                    #     f"Sheet {i}/{len(groups)} Ano cheio {len(items)} items {year} {version} - {grupo} {quadro} {account}"
                    # )
                    pass
                else:
                    print(f"Sheet de tamanho {len(items)}, o que está faltando?")
                    for item in items:
                        print(
                            f"{i}/{len(groups)} - {item[1].version} item {item[1].quarter}, grupo {item[1].grupo} account {item[1].account}"
                        )

            items.sort(key=lambda x: (x[0] or datetime.min))
            if account.startswith(self.year_end_prefixes):
                result.extend(self._adjust_year_end(items))
            elif account.startswith(self.cumulative_prefixes):
                result.extend(self._adjust_cumulative(items))
            else:
                result.extend(self._as_parsed(items))
        return result

    def _as_parsed(
        self, items: List[Tuple[datetime | None, ParsedStatementDTO]]
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
        self, items: List[Tuple[datetime | None, ParsedStatementDTO]]
    ) -> List[ParsedStatementDTO]:
        values: List[ParsedStatementDTO] = []
        cumulative = 0.0
        for idx, (dt, row) in enumerate(items):
            if not dt:
                # Data inválida ou None, mantém valor bruto
                val = row.value
            elif dt.month == 12:
                if idx == 0:
                    # Primeiro dezembro sem histórico anterior
                    # Mantém valor bruto (não temos base para ajustar)
                    val = row.value / 4  ## aproximation for first December
                    cumulative = 0.0  # Reset para próximo ano
                else:
                    # Demais dezembros: valor isolado = total - acumulado parcial
                    val = row.value - cumulative
                    cumulative = 0.0  # Reset para próximo ano
            else:
                # Meses intermediários: acumulando para subtrair em dezembro
                val = row.value
                cumulative += row.value

            # Recria DTO imutável
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
        self, items: List[Tuple[datetime | None, ParsedStatementDTO]]
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
