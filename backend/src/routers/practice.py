from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from src.database import get_db
from src.schemas.practice import (
    StartPracticeRequest,
    StartPracticeResponse,
    AnswerRequest,
    AnswerResponse,
    SessionStatusResponse,
    SessionHistoryResponse
)
from src.services.practice_service import PracticeService
from src.models.questionnaire import Questionnaire
from src.routers.auth import get_current_user
from src.models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/api/practice", tags=["practice"])

def get_practice_service():
    return PracticeService(
        model=None,
        api_url=None
    )

@router.post("/start", response_model=StartPracticeResponse)
async def start_practice(
    request: StartPracticeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: PracticeService = Depends(get_practice_service)
):
    """开始练习"""
    questionnaires_result = await db.execute(
        select(Questionnaire).where(
            Questionnaire.tool_id == request.tool_id,
            Questionnaire.user_id == current_user.id
        )
    )
    questionnaire = questionnaires_result.scalar_one_or_none()
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail="未找到对应的题本")
    
    import json
    questionnaire_content = json.loads(questionnaire.content)
    
    result = await service.start_practice(
        db=db,
        user_id=current_user.id,
        tool_id=request.tool_id,
        questionnaire_content=questionnaire_content
    )
    
    return result

@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    session_id: int,
    request: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: PracticeService = Depends(get_practice_service)
):
    """提交回答"""
    try:
        result = await service.submit_answer(
            db=db,
            session_id=session_id,
            user_answer=request.content,
            input_type=request.input_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: PracticeService = Depends(get_practice_service)
):
    """获取会话状态"""
    try:
        result = await service.get_session_status(db=db, session_id=session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: PracticeService = Depends(get_practice_service)
):
    """获取对话历史"""
    try:
        result = await service.get_session_history(db=db, session_id=session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
