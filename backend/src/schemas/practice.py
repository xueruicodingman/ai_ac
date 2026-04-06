from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Message(BaseModel):
    role: str  # "ai" | "user"
    content: str
    timestamp: str


class CompetencyInfo(BaseModel):
    name: str
    meaning: str
    behavior_criteria: List[Dict[str, str]]
    challenges: List[str]
    questions: List[str]
    followup_rules: str


class QuestionnaireData(BaseModel):
    theory: Optional[str] = None
    followup_strategy: Optional[str] = None
    competencies: List[CompetencyInfo]


class StartPracticeRequest(BaseModel):
    tool_id: str = "beh"


class StartPracticeResponse(BaseModel):
    session_id: int
    questionnaire: QuestionnaireData
    current_competency: Dict[str, Any]
    progress: Dict[str, int]


class AnswerRequest(BaseModel):
    content: str
    input_type: str = "text"  # "text" | "voice"


class AnswerResponse(BaseModel):
    next_action: str  # "continue" | "next_competency" | "finish"
    ai_message: Dict[str, Any]
    progress: Dict[str, int]


class SessionStatusResponse(BaseModel):
    session_id: int
    status: str
    current_competency_index: int
    total_competencies: int
    current_competency_name: str


class SessionHistoryResponse(BaseModel):
    session_id: int
    competency_name: str
    messages: List[Message]
    is_completed: bool
