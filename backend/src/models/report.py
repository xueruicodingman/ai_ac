from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from src.database import Base

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_id = Column(Integer, ForeignKey("assessment_records.id"), nullable=False)
    report_type = Column(String(50), nullable=False)
    candidate_id = Column(String(50), nullable=False)
    candidate_name = Column(String(100))
    scores_data = Column(Text)
    radar_chart_url = Column(String(500))
    total_score = Column(Numeric(5, 2))
    content = Column(Text, nullable=False)
    language = Column(String(20), default="zh")
    word_url = Column(String(500))
    pdf_url = Column(String(500))
    status = Column(String(20), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
