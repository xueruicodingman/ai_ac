from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.models.report import Report
from src.models.assessment_record import AssessmentRecord
from src.schemas.report import (
    ReportSaveRequest, ReportResponse
)
from src.services.report_service import ReportService
from src.services.user_settings_service import get_user_llm_config
from typing import List
import json

router = APIRouter(prefix="/api/reports", tags=["报告生成"])

@router.post("/generate/feedback")
async def generate_feedback_report(
    candidate_id: str,
    candidate_name: str,
    scores: dict,
    behaviors: dict = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    llm_config = await get_user_llm_config(db, current_user.id)
    
    if not llm_config["api_key"]:
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = ReportService(
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        api_url=llm_config["api_url"]
    )
    content = await service.generate_feedback_report(
        name=candidate_name,
        scores=scores,
        behaviors=behaviors
    )
    return {"success": True, "data": content}

@router.post("/generate/org")
async def generate_org_report(
    candidate_id: str,
    candidate_name: str,
    scores: dict,
    feedback_content: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    llm_config = await get_user_llm_config(db, current_user.id)
    
    if not llm_config["api_key"]:
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = ReportService(
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        api_url=llm_config["api_url"]
    )
    content = await service.generate_org_report(
        name=candidate_name,
        scores=scores,
        feedback_content=feedback_content
    )
    return {"success": True, "data": content}

@router.post("/generate/personal")
async def generate_personal_report(
    candidate_id: str,
    candidate_name: str,
    scores: dict,
    org_content: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    llm_config = await get_user_llm_config(db, current_user.id)
    
    if not llm_config["api_key"]:
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = ReportService(
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        api_url=llm_config["api_url"]
    )
    content = await service.generate_personal_report(
        name=candidate_name,
        scores=scores,
        org_content=org_content
    )
    return {"success": True, "data": content}

@router.get("", response_model=List[ReportResponse])
async def get_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Report).where(Report.user_id == current_user.id)
    )
    reports = result.scalars().all()
    
    return [
        ReportResponse(
            id=r.id, record_id=r.record_id, report_type=r.report_type,
            candidate_id=r.candidate_id, candidate_name=r.candidate_name,
            scores_data=json.loads(r.scores_data) if r.scores_data else None,
            radar_chart_url=r.radar_chart_url, total_score=float(r.total_score) if r.total_score else None,
            content=json.loads(r.content), language=r.language,
            word_url=r.word_url, pdf_url=r.pdf_url, status=r.status,
            created_at=str(r.created_at), updated_at=str(r.updated_at)
        )
        for r in reports
    ]

@router.post("", response_model=ReportResponse)
async def save_report(
    data: ReportSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Report).where(
            and_(
                Report.user_id == current_user.id,
                Report.report_type == data.report_type,
                Report.candidate_id == data.candidate_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    report = existing or Report(user_id=current_user.id)
    report.record_id = data.record_id
    report.report_type = data.report_type
    report.candidate_id = data.candidate_id
    report.candidate_name = data.candidate_name
    report.scores_data = json.dumps(data.scores_data) if data.scores_data else None
    report.radar_chart_url = data.radar_chart_url
    report.total_score = data.total_score
    report.content = json.dumps(data.content)
    report.language = data.language
    report.word_url = data.word_url
    report.pdf_url = data.pdf_url
    report.status = data.status
    
    if not existing:
        db.add(report)
    
    await db.commit()
    await db.refresh(report)
    
    return ReportResponse(
        id=report.id, record_id=report.record_id, report_type=report.report_type,
        candidate_id=report.candidate_id, candidate_name=report.candidate_name,
        scores_data=json.loads(report.scores_data) if report.scores_data else None,
        radar_chart_url=report.radar_chart_url, total_score=float(report.total_score) if report.total_score else None,
        content=json.loads(report.content), language=report.language,
        word_url=report.word_url, pdf_url=report.pdf_url, status=report.status,
        created_at=str(report.created_at), updated_at=str(report.updated_at)
    )
