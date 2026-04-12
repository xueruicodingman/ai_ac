import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from src.models.roleplay_practice import RolePlaySession, RolePlayMessage
from src.services.ai_service import AIService
from src.services.roleplay_rag import RolePlayRAG
from src.services.roleplay_prompt import RolePlayPromptBuilder
from src.config import settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一个角色扮演中的AI角色。请根据以下设定和上下文进行回复。

# 角色设定
{role_section}

# 相关上下文
{context_section}

# 对话历史
{history_section}

# 用户最新消息
{latest_section}

# 角色要求
1. 你扮演的是{subordinate_name},不是你自己
2. 保持角色设定中描述的性格、语言风格和行为模式
3. 根据当前情境和上下文做出符合角色的反应
4. 每次回复不超过100字
5. 如果用户结束对话，配合结束
"""


class RolePlayPracticeService:
    def __init__(self, model: str = None, api_url: str = None):
        self.ai_service = AIService(settings.API_KEY, model, api_url)
        self.rag = RolePlayRAG()
        self.prompt_builder = RolePlayPromptBuilder()

    async def start_session(
        self,
        db: AsyncSession,
        user_id: int,
        questionnaire_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """开始练习会话，初始化RAG"""
        role_play_content = questionnaire_content.get("role_play_content", {})
        if not role_play_content:
            role_play_content = questionnaire_content
        role_info = role_play_content.get("role_info", {})
        scenario = role_play_content.get("scenario", "")

        chunks = self.rag.chunk_text(scenario)
        self.rag.build_index(chunks)

        role_info_text = role_info.get("background", "") + role_info.get("personality", "")
        if role_info_text:
            intro_message = f"【场景】{scenario[:200]}\n\n你好，我是{role_info.get('subordinate_name', '相关角色')}。请问有什么可以帮您的？"
        else:
            intro_message = "你好，我是角色扮演中的AI角色。请问有什么可以帮您的？"

        session = RolePlaySession(
            user_id=user_id,
            tool_id="roleplay",
            questionnaire_content=json.dumps(questionnaire_content),
            status="in_progress",
            duration=1800,
            remaining_time=1800
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        message = RolePlayMessage(
            session_id=session.id,
            role="ai",
            content=intro_message,
            current_topic="开场",
            context_chunks=chunks[:3] if chunks else []
        )
        db.add(message)
        await db.commit()

        return {
            "session_id": session.id,
            "role_info": role_info,
            "first_message": {
                "content": intro_message,
                "role": "ai",
                "timestamp": datetime.utcnow().isoformat()
            },
            "remaining_time": 1800,
            "status": "in_progress"
        }

    async def submit_answer(
        self,
        db: AsyncSession,
        session_id: int,
        user_answer: str,
        input_type: str = "text"
    ) -> Dict[str, Any]:
        """提交回答，生成AI回复"""
        session = await db.get(RolePlaySession, session_id)
        if not session:
            raise ValueError("会话不存在")

        if session.status != "in_progress":
            raise ValueError("会话已结束")

        questionnaire_content = json.loads(session.questionnaire_content)
        role_info = questionnaire_content.get("role_play_content", {}).get("role_info", {})
        if not role_info:
            role_info = questionnaire_content.get("role_info", {})

        user_message = RolePlayMessage(
            session_id=session_id,
            role="user",
            content=user_answer
        )
        db.add(user_message)
        await db.commit()

        messages_result = await db.execute(
            select(RolePlayMessage)
            .where(RolePlayMessage.session_id == session_id)
            .order_by(RolePlayMessage.timestamp)
        )
        messages = messages_result.scalars().all()
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        retrieved_chunks = []
        if self.rag.index:
            retrieved = self.rag.search(user_answer, top_k=3)
            retrieved_chunks = retrieved

        prompt = self.prompt_builder.build(
            role_info=role_info,
            context_chunks=retrieved_chunks,
            conversation_history=conversation_history,
            latest_message=user_answer
        )

        full_prompt = SYSTEM_PROMPT.format(
            role_section=prompt.split("[话题上下文]")[0].replace("[角色定义]", "").replace("[用户最新答复]", ""),
            context_section=prompt.split("[话题上下文]")[1].split("[对话历史]")[0] if "[话题上下文]" in prompt else "",
            history_section=prompt.split("[对话历史]")[1].split("[用户最新答复]")[0] if "[对话历史]" in prompt else "",
            latest_section=prompt.split("[用户最新答复]")[1] if "[用户最新答复]" in prompt else "",
            subordinate_name=role_info.get("subordinate_name", "相关角色")
        )

        try:
            chat_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=full_prompt),
                HumanMessage(content=user_answer)
            ])
            chain = chat_prompt | self.ai_service.llm | StrOutputParser()
            ai_response = await chain.ainvoke({})
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            ai_response = "好的，我明白了。还有什么需要我配合的吗？"

        ai_message = RolePlayMessage(
            session_id=session_id,
            role="ai",
            content=ai_response,
            current_topic=retrieved_chunks[0].get("chunk", {}).get("chunk_type") if retrieved_chunks else None,
            context_chunks=[c.get("chunk") for c in retrieved_chunks[:3]] if retrieved_chunks else []
        )
        db.add(ai_message)
        await db.commit()

        remaining_time = max(0, session.remaining_time - 30)
        session.remaining_time = remaining_time

        return {
            "session_id": session_id,
            "ai_message": {
                "content": ai_response,
                "role": "ai",
                "timestamp": datetime.utcnow().isoformat()
            },
            "remaining_time": remaining_time,
            "status": session.status
        }

    async def get_history(
        self,
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        """获取对话历史"""
        session = await db.get(RolePlaySession, session_id)
        if not session:
            raise ValueError("会话不存在")

        questionnaire_content = json.loads(session.questionnaire_content)
        role_info = questionnaire_content.get("role_play_content", {}).get("role_info", {})
        if not role_info:
            role_info = questionnaire_content.get("role_info", {})

        messages_result = await db.execute(
            select(RolePlayMessage)
            .where(RolePlayMessage.session_id == session_id)
            .order_by(RolePlayMessage.timestamp)
        )
        messages = messages_result.scalars().all()

        message_list = [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "current_topic": m.current_topic,
                "context_chunks": m.context_chunks
            }
            for m in messages
        ]

        return {
            "session_id": session_id,
            "messages": message_list,
            "role_info": role_info
        }

    async def end_session(
        self,
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        """结束练习"""
        session = await db.get(RolePlaySession, session_id)
        if not session:
            raise ValueError("会话不存在")

        session.status = "ended"
        session.ended_at = datetime.utcnow()
        await db.commit()

        messages_result = await db.execute(
            select(RolePlayMessage)
            .where(RolePlayMessage.session_id == session_id)
        )
        messages_count = len(messages_result.scalars().all())

        return {
            "session_id": session_id,
            "status": "ended",
            "messages_count": messages_count
        }

    async def get_session_status(
        self,
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        """获取会话状态"""
        session = await db.get(RolePlaySession, session_id)
        if not session:
            raise ValueError("会话不存在")

        messages_result = await db.execute(
            select(RolePlayMessage)
            .where(RolePlayMessage.session_id == session_id)
        )
        messages = messages_result.scalars().all()
        latest_message = messages[-1] if messages else None

        return {
            "session_id": session_id,
            "status": session.status,
            "remaining_time": session.remaining_time,
            "messages_count": len(messages),
            "current_topic": latest_message.current_topic if latest_message else None
        }