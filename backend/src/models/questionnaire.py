from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database import Base

class Questionnaire(Base):
    __tablename__ = "questionnaires"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tool_id = Column(String(50), nullable=False)
    model_id = Column(Integer, ForeignKey("competency_models.id"), nullable=False)
    matrix_id = Column(Integer, ForeignKey("evaluation_matrices.id"), nullable=False)
    content = Column(Text, nullable=False)
    word_url = Column(String(500))
    pdf_url = Column(String(500))
    status = Column(String(20), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
