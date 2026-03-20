from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database import Base

class EvaluationMatrix(Base):
    __tablename__ = "evaluation_matrices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    model_id = Column(Integer, ForeignKey("competency_models.id"), nullable=False)
    tools = Column(Text, nullable=False)
    matrix = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
