import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from src.models.practice import PracticeSession, CompetencyRecord
from src.services.ai_service import AIService
from src.config import settings

logger = logging.getLogger(__name__)

FOLLOWUP_SYSTEM_PROMPT = """你是一个资深行为面试官，你需要基于被面试者的回答生成追问问题。

# 当前胜任力信息
能力名称：{competency_name}
能力含义：{ability_meaning}
关键行为标准：{behavior_criteria}
追问规则：{followup_rules}

# 对话历史
{conversation_history}

# 任务
1. 分析被面试者的回答，识别关键行为事件
2. 使用STAR法则（情境、任务、行动、结果）进行追问
3. 每次只生成1个追问问题，不超过50字
4. 如果已收集到足够的行为事实（至少1个完整的行为事件），返回 TERMINATE
5. 如果需要继续追问，返回 QUESTION + 追问内容

# 输出格式
TERMINATE - 已收集到足够行为事实
QUESTION: 追问问题内容
"""

TERMINATE_SYSTEM_PROMPT = """请判断是否已收集到足够的行为事实来评价该胜任力。

# 当前胜任力：{competency_name}
# 能力含义：{ability_meaning}
# 对话历史：
{conversation_history}

# 判定标准
满足以下任一条件即可终止：
1. 已收集到至少1个具体的行为事件（包含：情境、任务、行动、结果）
2. 已进行多轮追问挖掘，但用户无法提供更多具体例子或回答模糊

请返回JSON格式：
{{
    "should_terminate": true/false,
    "reason": "判断理由",
    "behavior_events_found": ["事件描述1", "事件描述2"]
}}"""


class PracticeService:
    def __init__(self, model: str = None, api_url: str = None):
        self.ai_service = AIService(settings.API_KEY, model, api_url)
    
    async def start_practice(
        self,
        db: AsyncSession,
        user_id: int,
        tool_id: str,
        questionnaire_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """开始练习会话"""
        session = PracticeSession(
            user_id=user_id,
            tool_id=tool_id,
            questionnaire_content=questionnaire_content,
            current_competency_index=0,
            status="in_progress"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        competencies = questionnaire_content.get("competencies", [])
        if not competencies:
            raise ValueError("问卷中无胜任力数据")
        
        first_competency = competencies[0]
        first_question = first_competency.get("questions", ["请分享一个你的工作经历"])[0]
        
        record = CompetencyRecord(
            session_id=session.id,
            competency_name=first_competency["name"],
            competency_index=0,
            messages=[{"role": "ai", "content": first_question, "timestamp": datetime.utcnow().isoformat()}],
            behavior_events=[],
            is_completed=False
        )
        db.add(record)
        await db.commit()
        
        return {
            "session_id": session.id,
            "questionnaire": questionnaire_content,
            "current_competency": {
                "index": 0,
                "name": first_competency["name"],
                "question": first_question
            },
            "progress": {
                "current": 1,
                "total": len(competencies)
            }
        }
    
    async def submit_answer(
        self,
        db: AsyncSession,
        session_id: int,
        user_answer: str,
        input_type: str = "text"
    ) -> Dict[str, Any]:
        """提交用户回答，返回AI追问或判断终止"""
        session = await db.get(PracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")
        
        if session.status != "in_progress":
            raise ValueError("会话已结束")
        
        competencies = session.questionnaire_content.get("competencies", [])
        current_index = session.current_competency_index
        current_competency = competencies[current_index]
        
        record_result = await db.execute(
            select(CompetencyRecord).where(
                CompetencyRecord.session_id == session_id,
                CompetencyRecord.competency_index == current_index
            )
        )
        record = record_result.scalar_one_or_none()
        
        if not record:
            raise ValueError("胜任力记录不存在")
        
        messages = record.messages or []
        messages.append({"role": "user", "content": user_answer, "timestamp": datetime.utcnow().isoformat()})
        record.messages = messages
        
        conversation_history = "\n".join([
            f"{'AI' if m['role'] == 'ai' else '用户'}: {m['content']}"
            for m in messages
        ])
        
        should_terminate = await self._check_terminate(
            current_competency,
            conversation_history
        )
        
        if should_terminate:
            record.is_completed = True
            await db.commit()
            
            if current_index + 1 >= len(competencies):
                session.status = "completed"
                await db.commit()
                return {
                    "next_action": "finish",
                    "ai_message": {
                        "content": "恭喜您已完成所有胜任力的行为事件访谈练习！",
                        "type": "completion"
                    },
                    "progress": {
                        "current": len(competencies),
                        "total": len(competencies)
                    }
                }
            else:
                session.current_competency_index = current_index + 1
                await db.commit()
                
                next_competency = competencies[current_index + 1]
                next_question = next_competency.get("questions", ["请分享"])[0]
                
                next_record = CompetencyRecord(
                    session_id=session_id,
                    competency_name=next_competency["name"],
                    competency_index=current_index + 1,
                    messages=[{"role": "ai", "content": next_question, "timestamp": datetime.utcnow().isoformat()}],
                    behavior_events=[],
                    is_completed=False
                )
                db.add(next_record)
                await db.commit()
                
                return {
                    "next_action": "next_competency",
                    "ai_message": {
                        "content": f"【{next_competency['name']}】{next_question}",
                        "type": "transition"
                    },
                    "progress": {
                        "current": current_index + 2,
                        "total": len(competencies)
                    }
                }
        
        followup_question = await self._generate_followup(
            current_competency,
            conversation_history
        )
        
        messages.append({"role": "ai", "content": followup_question, "timestamp": datetime.utcnow().isoformat()})
        record.messages = messages
        await db.commit()
        
        return {
            "next_action": "continue",
            "ai_message": {
                "content": followup_question,
                "type": "question"
            },
            "progress": {
                "current": current_index + 1,
                "total": len(competencies)
            }
        }
    
    async def _generate_followup(
        self,
        competency: Dict[str, Any],
        conversation_history: str
    ) -> str:
        """生成追问问题"""
        behavior_criteria_text = ""
        for bc in competency.get("behavior_criteria", [])[:3]:
            behavior_criteria_text += f"- {bc.get('title')}: {bc.get('description')}\n"
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=FOLLOWUP_SYSTEM_PROMPT.format(
                competency_name=competency.get("name", ""),
                ability_meaning=competency.get("meaning", ""),
                behavior_criteria=behavior_criteria_text,
                followup_rules=competency.get("followup_rules", ""),
                conversation_history=conversation_history
            )),
            HumanMessage(content="请根据对话历史生成追问问题")
        ])
        
        try:
            chain = prompt | self.ai_service.llm | StrOutputParser()
            response = await chain.ainvoke({})
        except Exception as e:
            logger.error(f"AI followup generation failed: {e}")
            return "感谢您的分享，这个胜任力的访谈已经完成。"
        
        if response.startswith("TERMINATE"):
            return "感谢您的分享，这个胜任力的访谈已经完成。"
        
        if response.startswith("QUESTION:"):
            return response[8:].strip()
        
        return response
    
    async def _check_terminate(
        self,
        competency: Dict[str, Any],
        conversation_history: str
    ) -> bool:
        """判断是否终止"""
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=TERMINATE_SYSTEM_PROMPT.format(
                competency_name=competency.get("name", ""),
                ability_meaning=competency.get("meaning", ""),
                conversation_history=conversation_history
            )),
            HumanMessage(content="请判断是否终止")
        ])
        
        try:
            chain = prompt | self.ai_service.llm | StrOutputParser()
            response = await chain.ainvoke({})
        except Exception as e:
            logger.error(f"AI termination check failed: {e}")
            return False
        
        try:
            result = json.loads(response)
            return result.get("should_terminate", False)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse termination response: {e}")
            return False
    
    async def get_session_status(
        self,
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        """获取会话状态"""
        session = await db.get(PracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")
        
        competencies = session.questionnaire_content.get("competencies", [])
        
        return {
            "session_id": session.id,
            "status": session.status,
            "current_competency_index": session.current_competency_index,
            "total_competencies": len(competencies),
            "current_competency_name": competencies[session.current_competency_index]["name"] if competencies else ""
        }
    
    async def get_session_history(
        self,
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        """获取当前胜任力的对话历史"""
        session = await db.get(PracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")
        
        current_index = session.current_competency_index
        
        record_result = await db.execute(
            select(CompetencyRecord).where(
                CompetencyRecord.session_id == session_id,
                CompetencyRecord.competency_index == current_index
            )
        )
        record = record_result.scalar_one_or_none()
        
        return {
            "session_id": session_id,
            "competency_name": record.competency_name if record else "",
            "messages": record.messages if record else [],
            "is_completed": record.is_completed if record else False
        }