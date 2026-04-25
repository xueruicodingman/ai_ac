import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.models.vision_practice import VisionPracticeSession
from src.config import settings
from src.utils.questionnaire_parser import parse_questionnaire_content

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个视觉练习中的AI分析师。请根据以下设定和上下文进行追问。

# 练习任务
{task_section}

# 题目分析要求
{analysis_section}

# 用户答案
{answer_section}

# 历史追问
{history_section}

# 角色要求
1. 你需要分析用户的答案，找出不足之处
2. 提出有针对性的追问，帮助用户深入思考
3. 每次追问不超过50字
4. 如果用户回答已经足够好，可以给出总结和建议
5. 如果用户结束对话，配合结束
"""


class VisionPracticeService:
    def __init__(self, api_key: str = None, model: str = None, api_url: str = None):
        from src.config import settings
        self.llm = ChatOpenAI(
            api_key=api_key or settings.API_KEY,
            model=model or settings.DEFAULT_MODEL,
            base_url=api_url or settings.DEFAULT_API_URL,
            temperature=0.7,
            streaming=True
        )
        self._api_key = api_key or settings.API_KEY

    def set_api_key(self, api_key: str):
        self._api_key = api_key
        self.llm.openai_api_key = api_key

    async def start_practice(
        self,
        db: AsyncSession,
        user_id: int,
        questionnaire_content: str,
        duration: int = 1800
    ) -> Dict[str, Any]:
        """开始练习会话"""
        # 解析questionnaire_content
        questionnaire_dict = parse_questionnaire_content(questionnaire_content)
        
        # 保存到数据库
        if isinstance(questionnaire_content, str):
            content_to_save = questionnaire_content
        else:
            content_to_save = json.dumps(questionnaire_content)
            
        session = VisionPracticeSession(
            user_id=user_id,
            questionnaire_content=content_to_save,
            status="running",
            remaining_time=duration
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # 获取练习任务信息
        task_info = questionnaire_dict.get("vision_prompt", {})
        task_title = task_info.get("title", "视觉练习")
        task_description = task_info.get("description", "")

        return {
            "session_id": session.id,
            "task_info": {
                "title": task_title,
                "description": task_description
            },
            "remaining_time": duration,
            "status": "running"
        }

    async def submit_answer(
        self,
        db: AsyncSession,
        session_id: int,
        user_answer: str
    ) -> Dict[str, Any]:
        """提交答案，生成AI追问"""
        session = await db.get(VisionPracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")

        if session.status not in ["running", "ai_interaction"]:
            raise ValueError("会话状态不允许提交答案")

        # 解析questionnaire_content
        questionnaire_dict = parse_questionnaire_content(session.questionnaire_content)
        
        # 更新用户答案
        if session.user_answer:
            # 追加到现有答案
            session.user_answer = session.user_answer + "\n---\n" + user_answer
        else:
            session.user_answer = user_answer

        # 解析历史分析
        challenge_analyses = session.challenge_analyses or []
        
        # 生成AI追问
        task_info = questionnaire_dict.get("vision_prompt", {})
        task_description = task_info.get("description", "")
        task_requirements = task_info.get("requirements", [])

        # 构建提示
        prompt = self._build_followup_prompt(
            task_description=task_description,
            requirements=task_requirements,
            user_answer=user_answer,
            history=challenge_analyses
        )

        try:
            chat_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=prompt),
                HumanMessage(content="请分析我的答案并提出追问")
            ])
            chain = chat_prompt | self.llm | StrOutputParser()
            ai_response = await chain.ainvoke({})
        except Exception as e:
            logger.error(f"AI followup generation failed: {e}")
            ai_response = "感谢你的回答。请进一步说明你的分析思路和判断依据。"

        # 更新分析历史
        challenge_analyses.append({
            "question": ai_response,
            "user_answer": user_answer,
            "timestamp": datetime.utcnow().isoformat()
        })
        session.challenge_analyses = challenge_analyses
        session.status = "ai_interaction"

        # 更新时间
        remaining_time = max(0, session.remaining_time - 60)

        await db.commit()

        return {
            "session_id": session_id,
            "ai_followup": {
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            },
            "remaining_time": remaining_time,
            "status": session.status
        }

    async def submit_followup(
        self,
        db: AsyncSession,
        session_id: int,
        user_response: str
    ) -> Dict[str, Any]:
        """提交追问回答"""
        session = await db.get(VisionPracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")

        if session.status != "ai_interaction":
            raise ValueError("当前不在追问状态")

        # 解析历史分析
        challenge_analyses = session.challenge_analyses or []
        
        # 添加追问回答到历史
        if challenge_analyses and len(challenge_analyses) > 0:
            last_analysis = challenge_analyses[-1]
            if "response" not in last_analysis:
                last_analysis["response"] = user_response
                last_analysis["response_timestamp"] = datetime.utcnow().isoformat()
                
                # 检查是否需要继续追问
                should_continue = await self._should_continue_interaction(
                    user_response=user_response,
                    history=challenge_analyses
                )
                
                if should_continue:
                    # 继续追问
                    questionnaire_dict = parse_questionnaire_content(session.questionnaire_content)
                    task_info = questionnaire_dict.get("vision_prompt", {})
                    task_description = task_info.get("description", "")
                    task_requirements = task_info.get("requirements", [])
                    
                    prompt = self._build_followup_prompt(
                        task_description=task_description,
                        requirements=task_requirements,
                        user_answer=session.user_answer or "",
                        history=challenge_analyses
                    )
                    
                    try:
                        chat_prompt = ChatPromptTemplate.from_messages([
                            SystemMessage(content=prompt),
                            HumanMessage(content="请继续分析并提出下一个追问")
                        ])
                        chain = chat_prompt | self.llm | StrOutputParser()
                        ai_response = await chain.ainvoke({})
                    except Exception as e:
                        logger.error(f"AI followup generation failed: {e}")
                        ai_response = None
                    
                    if ai_response:
                        challenge_analyses.append({
                            "question": ai_response,
                            "user_answer": session.user_answer,
                            "response": user_response,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        session.challenge_analyses = challenge_analyses
                        session.status = "ai_interaction"
                    else:
                        # 完成练习
                        session.status = "completed"
                else:
                    # 完成练习
                    session.status = "completed"
            else:
                # 已经回答过，添加新的一轮
                challenge_analyses.append({
                    "question": "请继续完成练习",
                    "response": user_response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                session.challenge_analyses = challenge_analyses
                session.status = "completed"
        else:
            session.status = "completed"

        remaining_time = max(0, session.remaining_time - 30)
        session.remaining_time = remaining_time

        await db.commit()

        return {
            "session_id": session_id,
            "ai_followup": {
                "content": challenge_analyses[-1].get("question") if challenge_analyses else None,
                "timestamp": datetime.utcnow().isoformat()
            },
            "remaining_time": remaining_time,
            "status": session.status
        }

    async def get_status(
        self,
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        """获取会话状态"""
        session = await db.get(VisionPracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")

        # 解析questionnaire_content
        questionnaire_dict = parse_questionnaire_content(session.questionnaire_content)
        task_info = questionnaire_dict.get("vision_prompt", {})

        return {
            "session_id": session_id,
            "status": session.status,
            "remaining_time": session.remaining_time,
            "user_answer": session.user_answer,
            "challenge_analyses": session.challenge_analyses,
            "task_info": {
                "title": task_info.get("title"),
                "description": task_info.get("description")
            }
        }

    def _build_followup_prompt(
        self,
        task_description: str,
        requirements: List[str],
        user_answer: str,
        history: List[Dict[str, Any]]
    ) -> str:
        """构建追问提示"""
        history_text = ""
        if history:
            for i, h in enumerate(history):
                q = h.get("question", "")
                a = h.get("user_answer", "")
                r = h.get("response", "")
                if q:
                    history_text += f"追问{i+1}：{q}\n"
                if a:
                    history_text += f"答案{i+1}：{a}\n"
                if r:
                    history_text += f"回应{i+1}：{r}\n"

        requirements_text = "\n".join([f"- {r}" for r in requirements]) if requirements else "无特定要求"

        prompt = f"""# 练习任务
{task_description}

# 分析要求
{requirements_text}

# 用户答案
{user_answer}

# 历史追问
{history_text}

请分析用户的答案，提出有针对性的追问。"""

        return prompt

    async def _should_continue_interaction(
        self,
        user_response: str,
        history: List[Dict[str, Any]]
    ) -> bool:
        """判断是否需要继续追问"""
        # 检查历史追问次数
        if len(history) >= 3:
            return False
        
        # 检查用户是否明确表示完成
        finish_keywords = ["完成", "结束", "没有了", "就这样", "完毕"]
        for keyword in finish_keywords:
            if keyword in user_response:
                return False
        
        # 简单判断回答长度
        if len(user_response) < 10:
            return True
        
        return True

    async def end_practice(
        self,
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        """结束练习"""
        session = await db.get(VisionPracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")

        session.status = "completed"
        await db.commit()

        return {
            "session_id": session_id,
            "status": "completed",
            "user_answer": session.user_answer,
            "challenge_analyses": session.challenge_analyses
        }