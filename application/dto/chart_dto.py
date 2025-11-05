from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel as PydanticModel


class ChartDTO(PydanticModel):
    """
    DTO genérico para representar um gráfico Plotly.

    - data: lista de traces Plotly (scatter, bar, etc.)
    - layout: configuração visual (títulos, eixos, etc.)
    - config: opções de interação (responsive, toImageButton, etc.)
    """

    data: List[Dict[str, Any]]
    layout: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
