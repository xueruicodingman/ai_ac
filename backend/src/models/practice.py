from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from src.database import Base


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tool_id = Column(String(50), nullable=False, default="beh")
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=True)
    questionnaire_content = Column(JSON, nullable=True)
    current_competency_index = Column(Integer, default=0)
    status = Column(String(20), default="in_progress")  # not_started, in_progress, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CompetencyRecord(Base):
    __tablename__ = "competency_records"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False, index=True)
    competency_name = Column(String(100), nullable=False)
    competency_index = Column(Integer, nullable=False)
    messages = Column(JSON, default=list)  # [{"role": "ai"|"user", "content": "...", "timestamp": "..."}]
    behavior_events = Column(JSON, default=list)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())