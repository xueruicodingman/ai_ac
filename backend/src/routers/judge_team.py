from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.services.judge_team_service import JudgeTeamService
from src.services.user_settings_service import get_user_llm_config
from typing import List, Dict, Any

router = APIRouter(prefix="/api/judge-teams", tags=["评委组管理"])

@router.get("")
async def get_judges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取评委配置（不区分工具）"""
    service = JudgeTeamService(db, current_user.id)
    judges = await service.get_judges()
    if not judges:
        return {"judges": []}
    return {"judges": judges}

@router.post("")
async def save_judges(
    judges: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """保存评委配置"""
    service = JudgeTeamService(db, current_user.id)
    result = await service.save_judges(judges)
    return {"success": True, "data": result}

@router.post("/generate")
async def generate_judges(
    count: int = Query(default=3, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """调用LLM生成评委角色与任务"""
    print(f"[generate_judges] user_id: {current_user.id}")
    llm_config = await get_user_llm_config(db, current_user.id)
    print(f"[generate_judges] llm_config: {llm_config}")
    
    api_key = llm_config.get("api_key")
    if not api_key or not api_key.strip():
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = JudgeTeamService(
        db, 
        user_id=current_user.id,
        api_key=llm_config.get("api_key"),
        api_url=llm_config.get("api_url"),
        model=llm_config.get("model")
    )
    try:
        judges = await service.generate_judges(count)
        return {"success": True, "data": {"judges": judges}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_msg = str(e)
        if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            raise HTTPException(status_code=504, detail="LLM响应超时，请稍后重试")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {error_msg}")