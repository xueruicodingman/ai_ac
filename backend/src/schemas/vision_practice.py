from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class StartVisionPracticeRequest(BaseModel):
    tool_id: str = "vision-practice"
    questionnaire_content: Optional[Dict[str, Any]] = None
    duration: Optional[int] = 1800


class StartVisionPracticeResponse(BaseModel):
    session_id: int
    task_info: Dict[str, Any]
    remaining_time: int
    status: str


class AnswerVisionPracticeRequest(BaseModel):
    content: str


class AnswerVisionPracticeResponse(BaseModel):
    session_id: int
    ai_followup: Dict[str, Any]
    remaining_time: int
    status: str


class FollowupVisionPracticeRequest(BaseModel):
    content: str


class FollowupVisionPracticeResponse(BaseModel):
    session_id: int
    ai_followup: Optional[Dict[str, Any]]
    remaining_time: int
    status: str


class VisionPracticeStatusResponse(BaseModel):
    session_id: int
    status: str
    remaining_time: int
    user_answer: Optional[str] = None
    challenge_analyses: Optional[List[Dict[str, Any]]] = None
    task_info: Optional[Dict[str, Any]] = None