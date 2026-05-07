from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.models.judge_handbook import JudgeHandbook
from src.schemas.handbook import (
    HandbookSaveRequest, HandbookResponse
)
from src.services.handbook_service import HandbookService
from src.services.user_settings_service import get_user_llm_config
from typing import List, Any, Dict, Optional
import json

router = APIRouter(prefix="/api/judge-handbooks", tags=["评委手册"])

@router.post("/generate")
async def generate_handbook(
    request: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    competency_model = request.get("competency_model", {})
    evaluation_matrix = request.get("evaluation_matrix", {})
    questionnaires = request.get("questionnaires", [])
    
    print(f"[DEBUG] Request body type: {type(request)}")
    print(f"[DEBUG] Request keys: {request.keys() if isinstance(request, dict) else 'not a dict'}")
    print(f"[DEBUG] competency_model: {competency_model}")
    print(f"[DEBUG] evaluation_matrix: {evaluation_matrix}")
    print(f"[DEBUG] questionnaires: {questionnaires}")
    
    llm_config = await get_user_llm_config(db, current_user.id)
    
    if not llm_config["api_key"] or not llm_config["api_key"].strip():
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = HandbookService(
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        api_url=llm_config["api_url"]
    )
    try:
        content = await service.generate(
            competency_model=competency_model,
            evaluation_matrix=evaluation_matrix,
            questionnaires=questionnaires
        )
        return {"success": True, "data": content}
    except Exception as e:
        import traceback
        print(f"Error generating handbook: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"生成评委手册失败: {str(e)}")

@router.post("/generate/{tool}")
async def generate_handbook_by_tool(
    tool: str,
    request: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    competency_model = request.get("competency_model", {})
    evaluation_matrix = request.get("evaluation_matrix", {})
    content = request.get("content", "")
    
    print(f"[DEBUG] Generate {tool}: content length = {len(content)}")
    
    llm_config = await get_user_llm_config(db, current_user.id)
    
    if not llm_config["api_key"] or not llm_config["api_key"].strip():
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = HandbookService(
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        api_url=llm_config["api_url"]
    )
    try:
        result = await service.generate_single_tool(
            tool=tool,
            content=content,
            competency_model=competency_model,
            evaluation_matrix=evaluation_matrix
        )
        return {"success": True, "data": {tool: result}}
    except Exception as e:
        import traceback
        print(f"Error generating handbook: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"生成评委手册失败: {str(e)}")

@router.get("", response_model=List[HandbookResponse])
async def get_handbook(
    tool: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if tool:
        result = await db.execute(
            select(JudgeHandbook).where(
                and_(JudgeHandbook.user_id == current_user.id, JudgeHandbook.tool == tool)
            )
        )
    else:
        result = await db.execute(
            select(JudgeHandbook).where(JudgeHandbook.user_id == current_user.id)
        )
    handbooks = result.scalars().all()
    
    if tool and not handbooks:
        raise HTTPException(status_code=404, detail="未找到该评委手册")
    
    if tool:
        handbook = handbooks[0] if handbooks else None
        if not handbook:
            raise HTTPException(status_code=404, detail="未找到评委手册")
        return [HandbookResponse(
            id=handbook.id,
            tool=handbook.tool,
            model_id=handbook.model_id,
            matrix_id=handbook.matrix_id,
            content=handbook.content,
            word_url=handbook.word_url,
            pdf_url=handbook.pdf_url,
            status=handbook.status,
            created_at=str(handbook.created_at),
            updated_at=str(handbook.updated_at)
        )]
    
    return [
        HandbookResponse(
            id=h.id,
            tool=h.tool,
            model_id=h.model_id,
            matrix_id=h.matrix_id,
            content=h.content,
            word_url=h.word_url,
            pdf_url=h.pdf_url,
            status=h.status,
            created_at=str(h.created_at),
            updated_at=str(h.updated_at)
        )
        for h in handbooks
    ]

@router.post("", response_model=HandbookResponse)
async def save_handbook(
    data: HandbookSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    print(f"[SAVE] save_handbook called, tool={data.tool}, user_id={current_user.id}")
    
    result = await db.execute(
        select(JudgeHandbook).where(
            and_(JudgeHandbook.user_id == current_user.id, JudgeHandbook.tool == data.tool)
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.model_id = data.model_id
        existing.matrix_id = data.matrix_id
        existing.content = data.content
        existing.word_url = data.word_url
        existing.pdf_url = data.pdf_url
        await db.commit()
        await db.refresh(existing)
        print(f"[SAVE] updated handbook id={existing.id}, updated_at={existing.updated_at}")
        return HandbookResponse(
            id=existing.id,
            tool=existing.tool,
            model_id=existing.model_id,
            matrix_id=existing.matrix_id,
            content=existing.content,
            word_url=existing.word_url,
            pdf_url=existing.pdf_url,
            status=existing.status,
            created_at=str(existing.created_at),
            updated_at=str(existing.updated_at)
        )
    
    handbook = JudgeHandbook(user_id=current_user.id, tool=data.tool)
    handbook.model_id = data.model_id
    handbook.matrix_id = data.matrix_id
    handbook.content = data.content
    handbook.word_url = data.word_url
    handbook.pdf_url = data.pdf_url
    db.add(handbook)
    await db.commit()
    await db.refresh(handbook)
    print(f"[SAVE] created handbook id={handbook.id}")
    
    return HandbookResponse(
        id=handbook.id,
        tool=handbook.tool,
        model_id=handbook.model_id,
        matrix_id=handbook.matrix_id,
        content=handbook.content,
        word_url=handbook.word_url,
        pdf_url=handbook.pdf_url,
        status=handbook.status,
        created_at=str(handbook.created_at),
        updated_at=str(handbook.updated_at)
    )
