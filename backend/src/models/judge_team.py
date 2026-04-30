from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from src.database import Base

class JudgeTeam(Base):
    __tablename__ = "judge_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tool = Column(String(20), nullable=False)  # beh/roleplay/lgd/case/vision
    judges = Column(JSON, nullable=False)  # [{"role": "主评委", "task": "...", "type": "judge"}, ...]
    # type字段: "judge"=评委, "actor"=演员
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())