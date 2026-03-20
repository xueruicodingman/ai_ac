from pydantic import BaseModel
from typing import Optional

class QuestionnaireGenerateRequest(BaseModel):
    tool_id: str
    competency_model: dict
    evaluation_matrix: dict
    api_key: str

class QuestionnaireSaveRequest(BaseModel):
    tool_id: str
    model_id: int
    matrix_id: int
    content: str
    word_url: Optional[str] = None
    pdf_url: Optional[str] = None

class QuestionnaireResponse(BaseModel):
    id: int
    tool_id: str
    model_id: int
    matrix_id: int
    content: str
    word_url: Optional[str]
    pdf_url: Optional[str]
    status: str
    created_at: str
    updated_at: str
