import logging
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from src.models.roleplay_practice import RolePlaySession
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roleplay", tags=["roleplay"])


async def verify_session_ownership(
    session_id: int,
    db: AsyncSession,
    current_user: User
) -> RolePlaySession:
    """Verify that the current user owns the session"""
    result = await db.execute(
        select(RolePlaySession).where(RolePlaySession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    return session


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
    await verify_session_ownership(session_id, db, current_user)
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


@router.post("/{session_id}/answer/stream")
async def submit_answer_stream(
    session_id: int,
    request: AnswerRolePlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """流式提交回答"""
    await verify_session_ownership(session_id, db, current_user)

    from src.services.user_settings_service import get_or_create_settings
    user_settings = await get_or_create_settings(db, current_user.id)
    api_key = user_settings.api_key or settings.API_KEY
    api_url = user_settings.api_url or settings.DEFAULT_API_URL
    model = user_settings.default_model or settings.DEFAULT_MODEL

    service = RolePlayPracticeService(model=model, api_url=api_url)
    service.set_api_key(api_key)

    async def event_generator():
        try:
            yield "data: {\"content\": \"\", \"done\": false}\n\n"
            
            async for chunk in service.stream_generate_response(
                db=db,
                session_id=session_id,
                user_answer=request.content,
                input_type=request.input_type
            ):
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
            
            yield "data: {\"content\": \"\", \"done\": true}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'content': '', 'done': true, 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{session_id}/status", response_model=RolePlayStatusResponse)
async def get_session_status(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: RolePlayPracticeService = Depends(get_roleplay_service)
):
    """获取会话状态"""
    await verify_session_ownership(session_id, db, current_user)
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
    await verify_session_ownership(session_id, db, current_user)
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
    await verify_session_ownership(session_id, db, current_user)
    try:
        result = await service.end_session(db=db, session_id=session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"End session failed: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")