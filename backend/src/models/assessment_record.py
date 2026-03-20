from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database import Base

class AssessmentRecord(Base):
    __tablename__ = "assessment_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    model_id = Column(Integer)
    matrix_id = Column(Integer)
    upload_file_id = Column(Integer)
    score_table = Column(Text, nullable=False)
    behavior_table = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
