from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.models.judge_handbook import JudgeHandbook
from src.schemas.handbook import (
    HandbookGenerateRequest, HandbookSaveRequest, HandbookResponse
)
from src.services.handbook_service import HandbookService
import json

router = APIRouter(prefix="/api/judge-handbooks", tags=["评委手册"])

@router.post("/generate")
async def generate_handbook(
    request: HandbookGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    service = HandbookService(api_key=request.api_key)
    content = await service.generate(
        competency_model=request.competency_model,
        evaluation_matrix=request.evaluation_matrix,
        questionnaires=request.questionnaires
    )
    return {"success": True, "data": {"content": content}}

@router.get("", response_model=HandbookResponse)
async def get_handbook(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(JudgeHandbook).where(JudgeHandbook.user_id == current_user.id)
    )
    handbook = result.scalar_one_or_none()
    if not handbook:
        raise HTTPException(status_code=404, detail="未找到评委手册")
    
    return HandbookResponse(
        id=handbook.id,
        model_id=handbook.model_id,
        matrix_id=handbook.matrix_id,
        questionnaire_ids=json.loads(handbook.questionnaires),
        content=handbook.content,
        word_url=handbook.word_url,
        pdf_url=handbook.pdf_url,
        status=handbook.status,
        created_at=str(handbook.created_at),
        updated_at=str(handbook.updated_at)
    )

@router.post("", response_model=HandbookResponse)
async def save_handbook(
    data: HandbookSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(JudgeHandbook).where(JudgeHandbook.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    handbook = existing or JudgeHandbook(user_id=current_user.id)
    handbook.model_id = data.model_id
    handbook.matrix_id = data.matrix_id
    handbook.questionnaires = json.dumps(data.questionnaire_ids)
    handbook.content = data.content
    handbook.word_url = data.word_url
    handbook.pdf_url = data.pdf_url
    
    if not existing:
        db.add(handbook)
    
    await db.commit()
    await db.refresh(handbook)
    
    return HandbookResponse(
        id=handbook.id,
        model_id=handbook.model_id,
        matrix_id=handbook.matrix_id,
        questionnaire_ids=json.loads(handbook.questionnaires),
        content=handbook.content,
        word_url=handbook.word_url,
        pdf_url=handbook.pdf_url,
        status=handbook.status,
        created_at=str(handbook.created_at),
        updated_at=str(handbook.updated_at)
    )
