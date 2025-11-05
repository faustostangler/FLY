from __future__ import annotations

from application.usecases.get_basic_chart import GetBasicChartUseCase


def chart_usecase_factory() -> GetBasicChartUseCase:
    """
    Factory para o UseCase de gráficos.

    Aqui você poderia injetar:
    - ConfigPort
    - LoggerPort
    - Repositórios
    - Serviços de domínio

    No primeiro passo, o UseCase não tem dependências externas.
    """
    return GetBasicChartUseCase()
