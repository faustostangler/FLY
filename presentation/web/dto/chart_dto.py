from pydantic import BaseModel
from typing import Any, Dict, List

class ChartDTO(BaseModel):
    title: str
    layout: Dict[str, Any]
    data: List[Dict[str, Any]]
