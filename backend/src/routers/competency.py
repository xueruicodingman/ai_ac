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
import json

router = APIRouter(prefix="/api/competency-models", tags=["胜任力模型"])

@router.post("/generate")
async def generate_competency_model(
    request: CompetencyGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    service = CompetencyService(api_key=request.api_key)
    result = await service.generate(
        background=request.background,
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
