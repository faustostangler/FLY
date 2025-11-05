from __future__ import annotations

from dataclasses import dataclass

from application.dto.chart_dto import ChartDTO


@dataclass
class GetBasicChartUseCase:
    """
    UseCase de exemplo que monta um ChartDTO simples.

    Depois você pode trocar os dados fixos por dados reais do domínio.
    """

    async def execute(self, chart_type: str) -> ChartDTO:
        # Aqui você poderia fazer:
        # - chamar serviços de domínio
        # - chamar repositórios via ports
        # No primeiro passo, vamos usar dados estáticos.

        if chart_type == "line":
            data = [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Preço",
                    "x": [1, 2, 3, 4],
                    "y": [10, 15, 13, 17],
                }
            ]
            title = "Gráfico de Linha de Exemplo"
        elif chart_type == "bar":
            data = [
                {
                    "type": "bar",
                    "name": "Volume",
                    "x": ["A", "B", "C"],
                    "y": [5, 3, 6],
                }
            ]
            title = "Gráfico de Barras de Exemplo"
        else:
            # tipo desconhecido: devolve algo simples
            data = [
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Default",
                    "x": [0, 1],
                    "y": [0, 1],
                }
            ]
            title = f"Gráfico default para tipo '{chart_type}'"

        layout = {
            "title": title,
            "xaxis": {"title": "Eixo X"},
            "yaxis": {"title": "Eixo Y"},
        }

        config = {
            "responsive": True,
        }

        return ChartDTO(data=data, layout=layout, config=config)
