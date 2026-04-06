from pydantic import BaseModel
from typing import List, Dict, Optional

class Tool(BaseModel):
    id: str
    name: str
    weight: int = 20
    enabled: bool = True

class MatrixGenerateRequest(BaseModel):
    competency_model: dict
    tools: Optional[List[Tool]] = None
    selected_tools: Optional[List[str]] = None

class MatrixSaveRequest(BaseModel):
    model_id: int
    tools: List[Tool]
    matrix: Dict[str, Dict[str, bool]]

class MatrixResponse(BaseModel):
    id: int
    model_id: int
    tools: List[Tool]
    matrix: Dict[str, Dict[str, bool]]
    created_at: str
    updated_at: str
