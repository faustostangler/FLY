# presentation/backend/schemas/chart_dto.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional


class PlotlyTraceDTO(BaseModel):
    """
    Trace genérico para Plotly.

    Mantém estrutura mínima para 80% dos gráficos (scatter, bar etc.).
    """
    x: List[Any]
    y: List[Any]
    type: str = Field(default="scatter")
    mode: Optional[str] = Field(default="lines")
    name: Optional[str] = None
    # campo extra para qualquer coisa específica de Plotly
    extra: Dict[str, Any] = Field(default_factory=dict)


class ChartDTO(BaseModel):
    """
    DTO de saída da API para o frontend Vue/Plotly.

    'data' é uma lista de traces Plotly,
    'layout' é um dict livre conforme API do Plotly.js.
    'meta' carrega metadados auxiliares (empresa, cache etc.).
    """

    data: List[PlotlyTraceDTO]
    layout: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
