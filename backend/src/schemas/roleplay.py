from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None
    current_topic: Optional[str] = None
    context_chunks: Optional[List[Dict]] = None


class StartRolePlayRequest(BaseModel):
    tool_id: str = "roleplay"
    questionnaire_content: Optional[Dict[str, Any]] = None


class StartRolePlayResponse(BaseModel):
    session_id: int
    role_info: Dict[str, Any]
    first_message: Dict[str, Any]
    remaining_time: int
    status: str


class AnswerRolePlayRequest(BaseModel):
    content: str
    input_type: str = "text"


class AnswerRolePlayResponse(BaseModel):
    session_id: int
    ai_message: Dict[str, Any]
    remaining_time: int
    status: str


class RolePlayStatusResponse(BaseModel):
    session_id: int
    status: str
    remaining_time: int
    messages_count: int
    current_topic: Optional[str] = None


class RolePlayHistoryResponse(BaseModel):
    session_id: int
    messages: List[Message]
    role_info: Dict[str, Any]