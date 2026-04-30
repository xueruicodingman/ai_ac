from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class EvaluationCriteriaBase(BaseModel):
    criteria_content: Dict[str, Any]


class EvaluationCriteriaCreate(EvaluationCriteriaBase):
    pass


class EvaluationCriteriaUpdate(BaseModel):
    criteria_content: Dict[str, Any]


class EvaluationCriteriaResponse(EvaluationCriteriaBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True