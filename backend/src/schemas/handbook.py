from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class HandbookGenerateRequest(BaseModel):
    competency_model: Dict[str, Any]
    evaluation_matrix: Dict[str, Any]
    questionnaires: List[Dict[str, Any]]

class HandbookSaveRequest(BaseModel):
    model_id: int
    matrix_id: int
    questionnaire_ids: List[int]
    content: str
    word_url: Optional[str] = None
    pdf_url: Optional[str] = None

class HandbookResponse(BaseModel):
    id: int
    model_id: int
    matrix_id: int
    questionnaire_ids: List[int]
    content: str
    word_url: Optional[str]
    pdf_url: Optional[str]
    status: str
    created_at: str
    updated_at: str
