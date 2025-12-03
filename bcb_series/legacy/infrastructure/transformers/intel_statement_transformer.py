"""Financial intelligence adapter implementing legacy parsing logic."""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

from domain.dto.statement_fetched_dto import StatementFetchedDTO
from domain.ports import ConfigPort, StatementTransformerPort
from domain.services import StatementClassificationService
from infrastructure.config.intel_criteria import load_intel_criteria_nodes


class IntelStatementTransformerAdapter(StatementTransformerPort):
    """Apply business rules to fetched statements."""

    def __init__(
        self,
        config: ConfigPort,
        classification_service: StatementClassificationService,
    ) -> None:
        self.classification_service = classification_service
        self.criteria_tree = load_intel_criteria_nodes()
        self.year_end_prefixes = config.transformers.intel_year_end_prefixes
        self.cumulative_prefixes = config.transformers.intel_cumulative_prefixes

    def transform(self, rows: Sequence[StatementFetchedDTO]) -> List[StatementFetchedDTO]:
        """Run the Intel transformation pipeline."""
        from infrastructure.utils.csv_utils import save_dtos_to_csv

        save_dtos_to_csv(rows, "raws_statements_stage_4_0.csv")

        transformed1 = self.classification_service.classify(
            list(rows), self.criteria_tree
        )
        save_dtos_to_csv(transformed1, "raws_statements_stage_4_1_standardized.csv")

        transformed2 = self.detect_and_correct_outliers(transformed1)
        save_dtos_to_csv(
            transformed2, "raws_statements_stage_4_2_corrected_outliers.csv"
        )

        return transformed2

    # Cleanup --------------------------------------------------------------
    def adjust_columns(
        self, rows: Iterable[StatementFetchedDTO]
    ) -> List[StatementFetchedDTO]:
        return [
            StatementFetchedDTO(
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
        self, rows: Iterable[StatementFetchedDTO]
    ) -> List[StatementFetchedDTO]:
        neighbor_count = 5  # Number of neighboring periods to consider
        epsilon = 1e-6

        # Agrupa por (grupo, account)
        groups: Dict[Tuple[str, str], List[StatementFetchedDTO]] = {}
        for row in rows:
            key = (row.grupo, row.account)
            groups.setdefault(key, []).append(row)

        results: List[StatementFetchedDTO] = []
        for items in groups.values():
            # Ordena por quarter (YYYY-MM-DD ordena lexicograficamente)
            items.sort(key=lambda r: r.quarter or "")
            corrected: List[StatementFetchedDTO] = []

            for i, row in enumerate(items):
                val = row.value

                # Determina janela adaptativa
                window_start = max(0, i - neighbor_count)
                window_end = min(len(items), i + neighbor_count + 1)

                # Listas de vizinhos
                vals_prev = [r.value for r in items[window_start:i]]
                vals_next = [r.value for r in items[i + 1 : window_end]]

                # Se não houver nenhum vizinho, mantém valor
                if not vals_prev and not vals_next:
                    corrected.append(row)
                    continue

                # Vamos testar janelas regressivamente (maior -> menor)
                windows_max = min(neighbor_count, len(items) - 1)
                new_val = val

                for n in range(windows_max, 0, -1):
                    vp = vals_prev[-n:] if len(vals_prev) >= 1 else []
                    vn = vals_next[:n] if len(vals_next) >= 1 else []

                    if vp and vn:
                        val_mean = (sum(vp) / len(vp) + sum(vn) / len(vn)) / 2
                    elif vp:
                        val_mean = sum(vp) / len(vp)
                    elif vn:
                        val_mean = sum(vn) / len(vn)
                    else:
                        continue  # Nenhum dado, não altera

                    # Teste de outlier pelo desvio
                    if val_mean and abs(val_mean * 1000 - val) < epsilon:
                        new_val = val_mean
                        break

                # Recria DTO imutável manualmente
                data = {**row.__dict__, "value": new_val}
                corrected.append(StatementFetchedDTO(**data))

            results.extend(corrected)

        return results
