from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.models.questionnaire import Questionnaire
from src.schemas.questionnaire import (
    QuestionnaireSaveRequest, QuestionnaireResponse
)
from src.services.questionnaire_service import QuestionnaireService
from src.services.user_settings_service import get_user_llm_config
from typing import List, Optional
import json

router = APIRouter(prefix="/api/questionnaires", tags=["题本生成"])

@router.post("/generate")
async def generate_questionnaire(
    tool_id: str,
    competency_model: dict = Body(...),
    evaluation_matrix: dict = Body(...),
    background_file_content: Optional[str] = Body(None),
    requirement: str = Body(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    print(f"[API] generate_questionnaire called, tool_id={tool_id}")
    print(f"[API] received background_file_content: {background_file_content[:100] if background_file_content else None}...")
    print(f"[API] background_file_content length: {len(background_file_content) if background_file_content else 0}")
    
    llm_config = await get_user_llm_config(db, current_user.id)
    
    if not llm_config["api_key"]:
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = QuestionnaireService(
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        api_url=llm_config["api_url"]
    )
    print(f"[API] Calling service.generate()...")
    content = await service.generate(
        tool_id=tool_id,
        competency_model=competency_model,
        evaluation_matrix=evaluation_matrix,
        background_file_content=background_file_content,
        requirement=requirement
    )
    print(f"[API] service.generate() completed, content length: {len(content)}")
    tool_info = service.get_tool_info(tool_id)
    return {"success": True, "data": {"content": content, **tool_info}}

@router.get("/tools")
async def get_tools():
    from src.services.questionnaire_service import TOOL_INFO
    return {"success": True, "data": TOOL_INFO}

@router.get("/{tool_id}", response_model=QuestionnaireResponse)
async def get_questionnaire(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Questionnaire).where(
            and_(
                Questionnaire.user_id == current_user.id,
                Questionnaire.tool_id == tool_id
            )
        )
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="未找到题本")
    
    return QuestionnaireResponse(
        id=q.id, tool_id=q.tool_id, model_id=q.model_id,
        matrix_id=q.matrix_id, content=q.content,
        word_url=q.word_url, pdf_url=q.pdf_url,
        status=q.status, created_at=str(q.created_at), updated_at=str(q.updated_at)
    )

@router.get("", response_model=List[QuestionnaireResponse])
async def get_all_questionnaires(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Questionnaire).where(Questionnaire.user_id == current_user.id)
    )
    questionnaires = result.scalars().all()
    
    return [
        QuestionnaireResponse(
            id=q.id, tool_id=q.tool_id, model_id=q.model_id,
            matrix_id=q.matrix_id, content=q.content,
            word_url=q.word_url, pdf_url=q.pdf_url,
            status=q.status, created_at=str(q.created_at), updated_at=str(q.updated_at)
        )
        for q in questionnaires
    ]

@router.post("", response_model=QuestionnaireResponse)
async def save_questionnaire(
    data: QuestionnaireSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Questionnaire).where(
            and_(
                Questionnaire.user_id == current_user.id,
                Questionnaire.tool_id == data.tool_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    q = existing or Questionnaire(user_id=current_user.id, tool_id=data.tool_id)
    q.model_id = data.model_id
    q.matrix_id = data.matrix_id
    q.content = data.content
    q.word_url = data.word_url
    q.pdf_url = data.pdf_url
    
    if not existing:
        db.add(q)
    
    await db.commit()
    await db.refresh(q)
    
    return QuestionnaireResponse(
        id=q.id, tool_id=q.tool_id, model_id=q.model_id,
        matrix_id=q.matrix_id, content=q.content,
        word_url=q.word_url, pdf_url=q.pdf_url,
        status=q.status, created_at=str(q.created_at), updated_at=str(q.updated_at)
    )
