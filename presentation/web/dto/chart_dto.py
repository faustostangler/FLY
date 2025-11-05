from pydantic import BaseModel as ORMBaseModel
from typing import Any, Dict, List

class ChartDTO(ORMBaseModel):
    title: str
    layout: Dict[str, Any]
    data: List[Dict[str, Any]]
