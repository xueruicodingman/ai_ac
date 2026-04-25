import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.schemas.vision_practice import (
    StartVisionPracticeRequest,
    StartVisionPracticeResponse,
    AnswerVisionPracticeRequest,
    AnswerVisionPracticeResponse,
    FollowupVisionPracticeRequest,
    FollowupVisionPracticeResponse,
    VisionPracticeStatusResponse
)
from src.services.vision_practice_service import VisionPracticeService
from src.routers.auth import get_current_user
from src.models.user import User
from src.models.vision_practice import VisionPracticeSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vision-practice", tags=["vision-practice"])


async def verify_session_ownership(
    session_id: int,
    db: AsyncSession,
    current_user: User
) -> VisionPracticeSession:
    """Verify that the current user owns the session"""
    result = await db.execute(
        select(VisionPracticeSession).where(VisionPracticeSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    return session


def get_vision_practice_service():
    return VisionPracticeService()


@router.post("/start", response_model=StartVisionPracticeResponse)
async def start_vision_practice(
    request: StartVisionPracticeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: VisionPracticeService = Depends(get_vision_practice_service)
):
    """开始视觉练习"""
    questionnaire_content = request.questionnaire_content

    if not questionnaire_content:
        questionnaire_content = {
            "vision_prompt": {
                "title": "个人愿景练习",
                "description": "请思考并描述你未来3-5年的职业愿景",
                "requirements": [
                    "描述你期望的工作状态",
                    "说明你的核心价值追求",
                    "阐述你的成长目标"
                ]
            }
        }

    try:
        result = await service.start_practice(
            db=db,
            user_id=current_user.id,
            questionnaire_content=questionnaire_content,
            duration=request.duration or 1800
        )
        return result
    except Exception as e:
        logger.error(f"Start vision practice failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/{session_id}/answer", response_model=AnswerVisionPracticeResponse)
async def submit_answer(
    session_id: int,
    request: AnswerVisionPracticeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: VisionPracticeService = Depends(get_vision_practice_service)
):
    """提交答案"""
    await verify_session_ownership(session_id, db, current_user)
    try:
        result = await service.submit_answer(
            db=db,
            session_id=session_id,
            user_answer=request.content
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Submit answer failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/{session_id}/followup", response_model=FollowupVisionPracticeResponse)
async def submit_followup(
    session_id: int,
    request: FollowupVisionPracticeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: VisionPracticeService = Depends(get_vision_practice_service)
):
    """提交追问回答"""
    await verify_session_ownership(session_id, db, current_user)
    try:
        result = await service.submit_followup(
            db=db,
            session_id=session_id,
            user_response=request.content
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Submit followup failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/{session_id}/status", response_model=VisionPracticeStatusResponse)
async def get_session_status(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: VisionPracticeService = Depends(get_vision_practice_service)
):
    """获取会话状态"""
    await verify_session_ownership(session_id, db, current_user)
    try:
        result = await service.get_status(db=db, session_id=session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get session status failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/{session_id}/end")
async def end_practice(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: VisionPracticeService = Depends(get_vision_practice_service)
):
    """结束练习"""
    await verify_session_ownership(session_id, db, current_user)
    try:
        result = await service.end_practice(db=db, session_id=session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"End practice failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")