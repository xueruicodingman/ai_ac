from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.models.evaluation_matrix import EvaluationMatrix
from src.models.competency_model import CompetencyModel
from src.schemas.matrix import (
    MatrixGenerateRequest, MatrixSaveRequest, MatrixResponse, Tool
)
from src.services.matrix_service import MatrixService
from src.services.user_settings_service import get_user_llm_config
import json

router = APIRouter(prefix="/api/evaluation-matrices", tags=["评估矩阵"])

@router.post("/generate")
async def generate_matrix(
    competency_model: dict,
    tools: list = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    llm_config = await get_user_llm_config(db, current_user.id)
    
    if not llm_config["api_key"]:
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    service = MatrixService(
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        api_url=llm_config["api_url"]
    )
    result = await service.generate(
        competency_model=competency_model,
        tools=tools
    )
    return {"success": True, "data": result}

@router.get("", response_model=MatrixResponse)
async def get_matrix(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(EvaluationMatrix).where(EvaluationMatrix.user_id == current_user.id)
    )
    matrix = result.scalar_one_or_none()
    if not matrix:
        raise HTTPException(status_code=404, detail="未找到评估矩阵")
    
    return MatrixResponse(
        id=matrix.id,
        model_id=matrix.model_id,
        tools=[Tool(**t) for t in json.loads(matrix.tools)],
        matrix=json.loads(matrix.matrix),
        created_at=str(matrix.created_at),
        updated_at=str(matrix.updated_at)
    )

@router.post("", response_model=MatrixResponse)
async def save_matrix(
    data: MatrixSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(EvaluationMatrix).where(EvaluationMatrix.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    matrix = existing or EvaluationMatrix(user_id=current_user.id)
    matrix.model_id = data.model_id
    matrix.tools = json.dumps([t.model_dump() for t in data.tools], ensure_ascii=False)
    matrix.matrix = json.dumps(data.matrix, ensure_ascii=False)
    
    if not existing:
        db.add(matrix)
    
    await db.commit()
    await db.refresh(matrix)
    
    return MatrixResponse(
        id=matrix.id,
        model_id=matrix.model_id,
        tools=[Tool(**t) for t in json.loads(matrix.tools)],
        matrix=json.loads(matrix.matrix),
        created_at=str(matrix.created_at),
        updated_at=str(matrix.updated_at)
    )

@router.get("/tools")
async def get_tools():
    service = MatrixService(api_key="")
    return {"success": True, "data": service.get_default_tools()}
