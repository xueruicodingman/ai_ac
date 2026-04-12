import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas.roleplay import (
    StartRolePlayRequest,
    StartRolePlayResponse,
    AnswerRolePlayRequest,
    AnswerRolePlayResponse,
    RolePlayStatusResponse,
    RolePlayHistoryResponse
)
from src.services.roleplay_practice_service import RolePlayPracticeService
from src.routers.auth import get_current_user
from src.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roleplay", tags=["roleplay"])


def get_roleplay_service():
    return RolePlayPracticeService(
        model=None,
        api_url=None
    )


@router.post("/start", response_model=StartRolePlayResponse)
async def start_roleplay(
    request: StartRolePlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: RolePlayPracticeService = Depends(get_roleplay_service)
):
    """开始角色扮演练习"""
    questionnaire_content = request.questionnaire_content
    
    if not questionnaire_content:
        questionnaire_content = {
            "role_play_content": {
                "role_info": {
                    "subordinate_name": "项目助理",
                    "background": "你是项目团队的助理",
                    "personality": "认真负责，积极主动",
                    "position": "支持项目经理的工作"
                },
                "scenario": "项目会议中，项目经理需要你协助处理一些事务"
            }
        }
    
    try:
        result = await service.start_session(
            db=db,
            user_id=current_user.id,
            questionnaire_content=questionnaire_content
        )
        return result
    except Exception as e:
        logger.error(f"Start roleplay failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/{session_id}/answer", response_model=AnswerRolePlayResponse)
async def submit_answer(
    session_id: int,
    request: AnswerRolePlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: RolePlayPracticeService = Depends(get_roleplay_service)
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
    except Exception as e:
        logger.error(f"Submit answer failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/{session_id}/status", response_model=RolePlayStatusResponse)
async def get_session_status(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: RolePlayPracticeService = Depends(get_roleplay_service)
):
    """获取会话状态"""
    try:
        result = await service.get_session_status(db=db, session_id=session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get session status failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/{session_id}/history", response_model=RolePlayHistoryResponse)
async def get_session_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: RolePlayPracticeService = Depends(get_roleplay_service)
):
    """获取对话历史"""
    try:
        result = await service.get_history(db=db, session_id=session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get session history failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/{session_id}/end")
async def end_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: RolePlayPracticeService = Depends(get_roleplay_service)
):
    """结束练习"""
    try:
        result = await service.end_session(db=db, session_id=session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"End session failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")