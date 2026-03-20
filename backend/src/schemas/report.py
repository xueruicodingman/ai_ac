from pydantic import BaseModel
from typing import Optional, Dict, Any

class FeedbackReportGenerateRequest(BaseModel):
    candidate_id: str
    candidate_name: str
    scores: Dict[str, float]
    behaviors: Optional[Dict[str, Any]] = None
    api_key: str

class OrgReportGenerateRequest(BaseModel):
    candidate_id: str
    candidate_name: str
    scores: Dict[str, float]
    feedback_content: dict
    api_key: str

class PersonalReportGenerateRequest(BaseModel):
    candidate_id: str
    candidate_name: str
    scores: Dict[str, float]
    org_content: dict
    api_key: str

class ReportSaveRequest(BaseModel):
    record_id: int
    report_type: str
    candidate_id: str
    candidate_name: Optional[str] = None
    scores_data: Optional[Dict[str, float]] = None
    radar_chart_url: Optional[str] = None
    total_score: Optional[float] = None
    content: dict
    language: str = "zh"
    word_url: Optional[str] = None
    pdf_url: Optional[str] = None
    status: str = "draft"

class ReportResponse(BaseModel):
    id: int
    record_id: int
    report_type: str
    candidate_id: str
    candidate_name: Optional[str]
    scores_data: Optional[Dict[str, float]]
    radar_chart_url: Optional[str]
    total_score: Optional[float]
    content: dict
    language: str
    word_url: Optional[str]
    pdf_url: Optional[str]
    status: str
    created_at: str
    updated_at: str
