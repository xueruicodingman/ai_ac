from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.models.competency_model import CompetencyModel
from src.schemas.competency import (
    CompetencyModelCreate, CompetencyModelResponse, CompetencyGenerateRequest
)
from src.services.competency_service import CompetencyService
from src.services.user_settings_service import get_user_llm_config
import json

router = APIRouter(prefix="/api/competency-models", tags=["胜任力模型"])

@router.post("/generate")
async def generate_competency_model(
    request: CompetencyGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 验证 num_competencies 必填
    if request.num_competencies is None or request.num_competencies < 1:
        raise HTTPException(status_code=400, detail="num_competencies 为必填参数")
    
    # 验证 background 和 specified_abilities 至少填一个
    has_background = request.background and len(request.background.strip()) > 0
    has_specified = request.specified_abilities and len(request.specified_abilities) > 0
    
    if not has_background and not has_specified:
        raise HTTPException(status_code=400, detail="background 和 specified_abilities 至少填写一个")
    
    llm_config = await get_user_llm_config(db, current_user.id)
    
    if not llm_config["api_key"]:
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = CompetencyService(
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        api_url=llm_config["api_url"]
    )
    result = await service.generate(
        background=request.background or "",
        specified_abilities=request.specified_abilities,
        num_competencies=request.num_competencies
    )
    return {"success": True, "data": result}

@router.get("", response_model=CompetencyModelResponse)
async def get_competency_model(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CompetencyModel).where(CompetencyModel.user_id == current_user.id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="未找到胜任力模型")
    
    return CompetencyModelResponse(
        id=model.id,
        name=model.name,
        dimensions=json.loads(model.dimensions),
        source_files=json.loads(model.source_files) if model.source_files else None,
        created_at=str(model.created_at),
        updated_at=str(model.updated_at)
    )

@router.post("", response_model=CompetencyModelResponse)
async def save_competency_model(
    data: CompetencyModelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CompetencyModel).where(CompetencyModel.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    model = existing or CompetencyModel(user_id=current_user.id)
    model.name = data.name
    model.dimensions = json.dumps([d.model_dump() for d in data.dimensions], ensure_ascii=False)
    model.source_files = json.dumps(data.source_files or [], ensure_ascii=False)
    
    if not existing:
        db.add(model)
    
    await db.commit()
    await db.refresh(model)
    
    return CompetencyModelResponse(
        id=model.id,
        name=model.name,
        dimensions=json.loads(model.dimensions),
        source_files=json.loads(model.source_files) if model.source_files else None,
        created_at=str(model.created_at),
        updated_at=str(model.updated_at)
    )
