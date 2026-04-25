from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from src.database import Base


class VisionPracticeSession(Base):
    __tablename__ = "vision_practice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    questionnaire_content = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    challenge_analyses = Column(JSON, nullable=True)
    status = Column(String(20), default="preparing")  # preparing, running, ai_interaction, completed
    remaining_time = Column(Integer, default=1800)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
