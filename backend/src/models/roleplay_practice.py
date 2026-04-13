from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from src.database import Base


class RolePlaySession(Base):
    __tablename__ = "roleplay_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tool_id = Column(String(50), nullable=False, default="roleplay")
    questionnaire_content = Column(Text, nullable=False)
    rag_index_data = Column(JSON)
    status = Column(String(20), default="in_progress")
    duration = Column(Integer, default=1800)
    remaining_time = Column(Integer, default=1800)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RolePlayMessage(Base):
    __tablename__ = "roleplay_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("roleplay_sessions.id"), nullable=False, index=True)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    current_topic = Column(String(100))
    context_chunks = Column(JSON)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())