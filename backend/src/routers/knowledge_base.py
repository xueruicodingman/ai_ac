from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.database import get_db
from src.models.user import User
from src.models.judge_handbook import JudgeHandbook
from src.routers.auth import get_current_user
from src.services.knowledge_base_service import KnowledgeBaseService
from src.services.user_settings_service import get_user_llm_config
from src.config import settings
from typing import Optional, Dict, Any
import json

router = APIRouter(prefix="/api/knowledge-base", tags=["知识库管理"])

@router.get("/{tool}")
async def get_knowledge_base(
    tool: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库"""
    service = KnowledgeBaseService(db, current_user.id)
    result = await service.get_knowledge_base(tool)
    if not result:
        return {
            "tool": tool,
            "chunk_config": {"strategy": "heading", "separator": "##", "max_length": 500},
            "chunks": [],
            "source_documents": []
        }
    return result

@router.post("/{tool}")
async def upload_document(
    tool: str,
    file: UploadFile = File(...),
    chunk_config: str = Form('{"strategy": "heading", "separator": "##", "max_length": 500}'),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传文档并切片"""
    content = await file.read()
    try:
        content = content.decode('utf-8')
    except:
        content = content.decode('gbk', errors='ignore')

    try:
        config = json.loads(chunk_config)
    except:
        config = {"strategy": "heading", "separator": "##", "max_length": 500}

    llm_config = await get_user_llm_config(db, current_user.id)
    api_key = llm_config.get("api_key") or settings.API_KEY if hasattr(settings, 'API_KEY') else None
    model = llm_config.get("model") or None
    api_url = llm_config.get("api_url") or None

    service = KnowledgeBaseService(db, current_user.id, api_key=api_key, model=model, api_url=api_url)
    try:
        result = await service.upload_document(
            tool=tool,
            file_name=file.filename,
            file_content=content,
            chunk_config=config
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{tool}/use-handbook")
async def use_handbook_as_source(
    tool: str,
    chunk_config: Dict[str, Any] = {"strategy": "heading", "separator": "##", "max_length": 500},
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """使用评委手册内容作为知识库"""
    result = await db.execute(
        select(JudgeHandbook).where(JudgeHandbook.user_id == current_user.id)
    )
    handbook = result.scalar_one_or_none()

    if not handbook or not handbook.content:
        raise HTTPException(status_code=400, detail="未找到评委手册内容，请先生成评委手册")

    try:
        handbook_data = json.loads(handbook.content)
    except:
        raise HTTPException(status_code=400, detail="评委手册内容格式错误")

    tool_handbook = next((h for h in handbook_data if h.get("tool") == tool), None)
    if not tool_handbook:
        raise HTTPException(status_code=400, detail=f"未找到 tool={tool} 的评委手册")

    handbook_content = tool_handbook.get("judge_content", "")
    if not handbook_content:
        raise HTTPException(status_code=400, detail="该工具的评委手册内容为空")

    llm_config = await get_user_llm_config(db, current_user.id)
    api_key = llm_config.get("api_key") or settings.API_KEY if hasattr(settings, 'API_KEY') else None
    model = llm_config.get("model") or None
    api_url = llm_config.get("api_url") or None

    service = KnowledgeBaseService(db, current_user.id, api_key=api_key, model=model, api_url=api_url)
    result = await service.use_handbook_as_source(tool, chunk_config, handbook_content)
    return {"success": True, "data": result}

@router.put("/{tool}/chunks")
async def update_chunks(
    tool: str,
    chunk_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新切片配置并重新切片"""
    llm_config = await get_user_llm_config(db, current_user.id)
    api_key = llm_config.get("api_key") or settings.API_KEY if hasattr(settings, 'API_KEY') else None
    model = llm_config.get("model") or None
    api_url = llm_config.get("api_url") or None

    service = KnowledgeBaseService(db, current_user.id, api_key=api_key, model=model, api_url=api_url)
    result = await service.update_chunks(tool, chunk_config)
    return {"success": True, "data": result}

@router.put("/{tool}/chunks/{chunk_id}")
async def update_chunk_content(
    tool: str,
    chunk_id: str,
    chunk_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新单个切片的内容"""
    service = KnowledgeBaseService(db, current_user.id)
    result = await service.update_chunk_content(tool, chunk_id, chunk_data)
    return {"success": True, "data": result}

@router.delete("/{tool}/chunks/{chunk_id}")
async def delete_chunk(
    tool: str,
    chunk_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除单个切片"""
    service = KnowledgeBaseService(db, current_user.id)
    result = await service.delete_chunk(tool, chunk_id)
    return {"success": True, "data": result}

@router.post("/{tool}/chunks")
async def add_chunk(
    tool: str,
    chunk_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """新增切片"""
    service = KnowledgeBaseService(db, current_user.id)
    result = await service.add_chunk(tool, chunk_data)
    return {"success": True, "data": result}

@router.delete("/{tool}")
async def delete_knowledge_base(
    tool: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除知识库"""
    service = KnowledgeBaseService(db, current_user.id)
    result = await service.delete_knowledge_base(tool)
    return {"success": True, "deleted": result}