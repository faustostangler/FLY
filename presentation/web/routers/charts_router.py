from fastapi import APIRouter, Depends
from presentation.web.dto.chart_dto import ChartDTO

router = APIRouter(prefix="/api/charts", tags=["charts"])

@router.get("/{chart_type}", response_model=ChartDTO)
async def get_chart(chart_type: str):
    # Simulação temporária (lógica real virá da camada application)
    return ChartDTO(
        title=f"Chart: {chart_type}",
        layout={"xaxis": {"title": "Time"}, "yaxis": {"title": "Value"}},
        data=[{"x": [1, 2, 3], "y": [10, 20, 15], "type": "line"}]
    )
