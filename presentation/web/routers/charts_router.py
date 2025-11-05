from __future__ import annotations

from fastapi import APIRouter, Depends

from application.dto.chart_dto import ChartDTO
from application.usecases.get_basic_chart import GetBasicChartUseCase
from infrastructure.factories.web_chart_factory import chart_usecase_factory

router = APIRouter(
    prefix="/api/charts",
    tags=["charts"],
)


@router.get("/{chart_type}", response_model=ChartDTO)
async def get_chart(
    chart_type: str,
    usecase: GetBasicChartUseCase = Depends(chart_usecase_factory),
) -> ChartDTO:
    """
    Endpoint fino:
    - Recebe o tipo do gráfico (chart_type)
    - Pede o UseCase via Depends (inversão de dependência)
    - Retorna ChartDTO, que o FastAPI serializa para JSON
    """
    return await usecase.execute(chart_type)
