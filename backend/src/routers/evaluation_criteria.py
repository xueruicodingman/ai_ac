import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.schemas.evaluation_criteria import (
    EvaluationCriteriaCreate,
    EvaluationCriteriaUpdate,
    EvaluationCriteriaResponse
)
from src.models.evaluation_criteria import EvaluationCriteria
from src.routers.auth import get_current_user
from src.models.user import User

router = APIRouter(prefix="/api/evaluation-criteria", tags=["evaluation-criteria"])


@router.get("", response_model=EvaluationCriteriaResponse)
async def get_evaluation_criteria(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取评价标准"""
    result = await db.execute(
        select(EvaluationCriteria).where(
            EvaluationCriteria.user_id == current_user.id
        ).order_by(EvaluationCriteria.id.desc()).limit(1)
    )
    criteria = result.scalar_one_or_none()
    
    if not criteria:
        default_content = {
            "levels": [
                {"name": "优", "score_min": 9, "score_max": 10, "description": "【完全体现】且其中2条行为标准的行为质量为【高】"},
                {"name": "良", "score_min": 7, "score_max": 8, "description": "【完全体现】且仅有1条行为标准的行为质量为【高】或【部分体现】且其中2条行为标准的行为质量为【高】"},
                {"name": "合格", "score_min": 5, "score_max": 6, "description": "【完全体现】且其中0条行为标准的行为质量为【高】或【部分体现】且其中1条行为标准的行为质量为【高】或【部分体现】且其中0条行为标准的行为质量为【高】或【稍微体现】且其中1条行为标准的行为质量为【高】"},
                {"name": "不合格", "score_min": 0, "score_max": 4, "description": "【稍微体现】且其中0条行为标准的行为质量为【高】或【未体现】"}
            ],
            "quantity": [
                {"name": "未体现", "count": 0, "description": "学员在练习中行为体现出其中0条行为标准"},
                {"name": "稍微体现", "count": 1, "description": "学员在练习中行为体现出其中1条行为标准"},
                {"name": "部分体现", "count": 2, "description": "学员在练习中行为体现出其中2条行为标准"},
                {"name": "完全体现", "count": 3, "description": "学员在练习中行为体现出其中3条行为标准"}
            ],
            "quality": [
                "学员在练习中，反复、频繁地出现反映胜任力某条行为标准的行为，均以正向的行为为主",
                "在某个压力场景下，依然能够展现反映胜任力某条行为标准的行为",
                "学员在练习中，体现出反映胜任力某条行为标准非常规的行为，例如在某个场景下，很少有人能够体现出这样的行为"
            ],
            "rules": [
                {"name": "评委打分", "description": "只允许取整数打分"},
                {"name": "分差限制", "description": "两位评委之间的分差不允许超过1分"}
            ]
        }
        
        new_criteria = EvaluationCriteria(
            user_id=current_user.id,
            criteria_content=default_content
        )
        db.add(new_criteria)
        await db.commit()
        await db.refresh(new_criteria)
        return new_criteria
    
    return criteria


@router.post("", response_model=EvaluationCriteriaResponse)
async def save_evaluation_criteria(
    criteria_data: EvaluationCriteriaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存评价标准（更新或新建）"""
    result = await db.execute(
        select(EvaluationCriteria).where(
            EvaluationCriteria.user_id == current_user.id
        ).order_by(EvaluationCriteria.id.desc()).limit(1)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.criteria_content = criteria_data.criteria_content
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        new_criteria = EvaluationCriteria(
            user_id=current_user.id,
            criteria_content=criteria_data.criteria_content
        )
        db.add(new_criteria)
        await db.commit()
        await db.refresh(new_criteria)
        return new_criteria