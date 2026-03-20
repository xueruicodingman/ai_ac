from pydantic import BaseModel
from typing import List, Optional

class HandbookGenerateRequest(BaseModel):
    competency_model: dict
    evaluation_matrix: dict
    questionnaires: List[dict]
    api_key: str

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
