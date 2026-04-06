from pydantic import BaseModel
from typing import List, Optional

class BehaviorCriterion(BaseModel):
    id: str
    title: str
    description: str

class Dimension(BaseModel):
    id: str
    name: str
    meaning: str
    behavior_criteria: List[BehaviorCriterion]

class CompetencyModelCreate(BaseModel):
    name: str = "胜任力模型"
    dimensions: List[Dimension]
    source_files: Optional[List[str]] = None

class CompetencyModelResponse(BaseModel):
    id: int
    name: str
    dimensions: List[Dimension]
    source_files: Optional[List[str]] = None
    created_at: str
    updated_at: str

class CompetencyGenerateRequest(BaseModel):
    background: Optional[str] = None
    files: Optional[List[str]] = None
    specified_abilities: Optional[List[str]] = None
    num_competencies: int = 5
