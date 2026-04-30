import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from src.database import get_db
from src.models.evaluation_matrix import EvaluationMatrix
from src.models.practice import PracticeSession, CompetencyRecord
from src.models.judge_team import JudgeTeam
from src.models.user import User
from src.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/behavior-evaluation", tags=["behavior-evaluation"])


class ToolInfo(BaseModel):
    id: str
    name: str


class CompetencyInMatrix(BaseModel):
    name: str
    meaning: str
    behavior_criteria: List[Dict[str, Any]]


class ToolWithCompetencies(BaseModel):
    tool_id: str
    tool_name: str
    competencies: List[CompetencyInMatrix]


@router.get("/tools")
async def get_user_tools_with_competencies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户评估矩阵中选中的测评工具及其胜任力"""
    from src.models.evaluation_matrix import EvaluationMatrix
    from src.models.competency_model import CompetencyModel
    
    result = await db.execute(
        select(EvaluationMatrix).where(EvaluationMatrix.user_id == current_user.id)
    )
    matrix = result.scalar_one_or_none()
    
    if not matrix:
        return {"tools": []}
    
    tools = json.loads(matrix.tools) if matrix.tools else []
    matrix_data = json.loads(matrix.matrix) if matrix.matrix else {}
    
    model_result = await db.execute(
        select(CompetencyModel).where(CompetencyModel.user_id == current_user.id)
    )
    competency_model = model_result.scalar_one_or_none()
    
    competency_details = {}
    if competency_model and competency_model.dimensions:
        dims = json.loads(competency_model.dimensions) if isinstance(competency_model.dimensions, str) else competency_model.dimensions
        for dim in dims:
            competency_details[dim.get("name", "")] = {
                "meaning": dim.get("meaning", ""),
                "behavior_criteria": dim.get("behavior_criteria", [])
            }
    
    result_tools = []
    for tool in tools:
        tool_id = tool.get("id")
        tool_name = tool.get("name", "")
        
        enabled_competencies = []
        for comp_name, comp_tools in matrix_data.items():
            if comp_tools.get(tool_id):
                comp_info = competency_details.get(comp_name, {})
                enabled_competencies.append({
                    "name": comp_name,
                    "meaning": comp_info.get("meaning", ""),
                    "behavior_criteria": comp_info.get("behavior_criteria", [])
                })
        
        if enabled_competencies:
            result_tools.append({
                "tool_id": tool_id,
                "tool_name": tool_name,
                "competencies": enabled_competencies
            })
    
    return {"tools": result_tools}


@router.get("/sessions/{tool_id}")
async def get_practice_sessions_by_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定测评工具的练习记录"""
    result = await db.execute(
        select(PracticeSession).where(
            PracticeSession.user_id == current_user.id,
            PracticeSession.tool_id == tool_id,
            PracticeSession.status == "completed"
        ).order_by(PracticeSession.id.desc())
    )
    sessions = result.scalars().all()
    
    session_list = []
    for session in sessions:
        session_list.append({
            "session_id": session.id,
            "tool_id": session.tool_id,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "status": session.status
        })
    
    return {"sessions": session_list}


@router.get("/session/{session_id}")
async def get_session_evaluation_data(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话的完整评价数据（原始记录+行为提取）"""
    session = await db.get(PracticeSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    questionnaire = session.questionnaire_content or {}
    competencies_in_questionnaire = questionnaire.get("competencies", [])
    
    comp_names = [c.get("name") for c in competencies_in_questionnaire]
    
    result = await db.execute(
        select(CompetencyRecord).where(
            CompetencyRecord.session_id == session_id
        ).order_by(CompetencyRecord.competency_index)
    )
    records = result.scalars().all()
    
    competency_evaluations = []
    for comp_name in comp_names:
        matching_record = None
        for record in records:
            if record.competency_name == comp_name:
                matching_record = record
                break
        
        comp_info = next((c for c in competencies_in_questionnaire if c.get("name") == comp_name), {})
        
        behavior_events = []
        if matching_record and matching_record.behavior_events:
            for event in matching_record.behavior_events:
                extracted = event.get("extracted", {})
                behavior_events.append({
                    "situation": extracted.get("situation", ""),
                    "target": extracted.get("target", ""),
                    "role": extracted.get("role", ""),
                    "challenge": extracted.get("challenge", ""),
                    "thinking": extracted.get("thinking", ""),
                    "action": extracted.get("action", ""),
                    "result": extracted.get("result", ""),
                    "reflection": extracted.get("reflection", "")
                })
        
        competency_evaluations.append({
            "name": comp_name,
            "meaning": comp_info.get("meaning", ""),
            "behavior_criteria": comp_info.get("behavior_criteria", []),
            "extracted_behaviors": behavior_events
        })
    
    all_messages = []
    for record in records:
        msgs = record.messages or []
        for msg in msgs:
            all_messages.append({
                "role": msg.get("role"),
                "content": msg.get("content"),
                "timestamp": msg.get("timestamp")
            })
    
    all_messages.sort(key=lambda x: x.get("timestamp", "") if x.get("timestamp") else "")
    
    original_records = []
    for msg in all_messages:
        original_records.append(f"{'面试官' if msg.get('role') == 'ai' else '考生'}: {msg.get('content', '')}")
    
    # 获取评委组信息（优先使用对应工具的评委，没有则使用default）
    judges = []
    judge_result = await db.execute(
        select(JudgeTeam).where(
            JudgeTeam.user_id == current_user.id,
            JudgeTeam.tool == session.tool_id
        )
    )
    judge_team = judge_result.scalar_one_or_none()
    
    if not judge_team or not judge_team.judges:
        # fallback到default评委组
        judge_result = await db.execute(
            select(JudgeTeam).where(
                JudgeTeam.user_id == current_user.id,
                JudgeTeam.tool == "default"
            )
        )
        judge_team = judge_result.scalar_one_or_none()
    
    if judge_team and judge_team.judges:
        judges = judge_team.judges
    
    # 获取评价结果
    evaluation_results = session.evaluation_results or {}
    total_score = session.total_score
    
    return {
        "session_id": session_id,
        "tool_id": session.tool_id,
        "judges": judges,
        "competencies": competency_evaluations,
        "evaluation_results": evaluation_results,
        "total_score": total_score,
        "original_records": original_records
    }