import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from src.models.practice import PracticeSession, CompetencyRecord
from src.config import settings
from src.utils.questionnaire_parser import parse_questionnaire_content

logger = logging.getLogger(__name__)

BEHAVIOR_EXTRACT_PROMPT = """请从以下对话中提取行为事件的关键信息。

## 对话内容
{conversation}

## 提取要求
请提取以下8个维度的信息，如果某维度没有相关信息，请标注"未提及"：

1. Situation（情境/背景）：事件发生的具体环境和背景
2. Target（任务/目标）：面临的任务、要解决的问题或目标
3. Role（角色）：在该事件中的职责或角色
4. Challenge（挑战）：完成目标或解决问题面临的困难和挑战
5. Thinking（思考）：当时的思考过程、决策依据
6. Action（行动）：采取的具体措施和行动
7. Result（结果）：行动后的结果和成效
8. Reflection（反思）：事后的总结和反思，做得好的和需要改进的

## 输出格式
请直接输出以下JSON格式（不要有其他内容）：
```json
{
  "situation": "...",
  "target": "...",
  "role": "...",
  "challenge": "...",
  "thinking": "...",
  "action": "...",
  "result": "...",
  "reflection": "..."
}
```"""

FOLLOWUP_QUESTION_PROMPT = """你是一位资深行为面试官。请根据以下信息生成下一个追问问题。

## 胜任力信息
胜任力名称：{competency_name}
胜任力含义：{competency_meaning}
行为标准：{behavior_criteria}

## 当前状态
当前阶段：{current_phase}
已提取的行为事件：{behavior_event}
当前评估状态：{evaluation}

## 对话历史
{conversation}

## 追问要求
1. 根据当前访谈阶段和用户回答生成针对性的追问
2. 问题要自然、简洁，不超过30字
3. 不要使用STAR、 Situation、Role 等技术术语
4. 如果用户说没有相关经历，换一个角度继续追问
5. 如果已经获得完整STAR+Reflection，可以结束当前胜任力

## 输出格式
直接输出问题内容，不要有其他格式。"""

BEHAVIOR_EVALUATE_PROMPT = """请根据以下信息评估行为事件访谈的质量。

## 胜任力信息
胜任力名称：{competency_name}
胜任力含义：{competency_meaning}
行为标准：{behavior_criteria}

## 对话内容
{conversation}

## 提取的行为事件
{behavior_event}

## 评估维度
请对以下四个维度进行评估：

1. Has_experience（是否有相关经历）：用户是否有与目标胜任力相关的真实经历？
   - 值：true/false
   - 说明：用户描述的经历是否真实存在，还是在敷衍或编造

2. Match_competency（胜任力匹配）：用户描述的行为事件是否与目标胜任力相关？评估是否体现了目标胜任力所要求的行为特征。
   - 值：true/false
   - 说明：为什么匹配或不匹配

3. Detail_sufficient（细节充分）：行为事件的描述是否足够详细？包括情境、任务、行动、结果等关键要素是否完整。
   - 值：true/false
   - 说明：哪些细节充分，哪些不足

4. Logic_right（逻辑正确）：整个事件的描述是否符合逻辑？时间顺序、因果关系是否清晰合理。
   - 值：true/false
   - 说明：逻辑是否合理

## 输出格式
请直接输出以下JSON格式（不要有其他内容）：
```json
{
  "has_experience": {"value": true/false, "reason": "..."},
  "match_competency": {"value": true/false, "reason": "..."},
  "detail_sufficient": {"value": true/false, "reason": "..."},
  "logic_right": {"value": true/false, "reason": "..."}
}
```"""


class PracticeService:
    def __init__(self, api_key: str, model: str = None, api_url: str = None):
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=api_url or settings.DEFAULT_API_URL,
            model=model or settings.DEFAULT_MODEL,
            temperature=0.7
        )
    
    async def start_practice(
        self,
        db: AsyncSession,
        user_id: int,
        tool_id: str,
        questionnaire_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 解析questionnaire_content（支持新格式JSON、旧格式JSON和文本）
        questionnaire_content = parse_questionnaire_content(
            questionnaire_content if isinstance(questionnaire_content, str) else json.dumps(questionnaire_content)
        )
        
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
            is_completed=False,
            current_phase="init",
            question_count=1,
            event_count=0,
            used_question_indices=[0]
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
        session = await db.get(PracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")
        
        if session.status != "in_progress":
            raise ValueError("会话已结束")
        
        # 解析questionnaire_content（支持新格式JSON、旧格式JSON和文本）
        questionnaire_content = parse_questionnaire_content(
            session.questionnaire_content if isinstance(session.questionnaire_content, str) else json.dumps(session.questionnaire_content)
        )
        competencies = questionnaire_content.get("competencies", [])
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
        
        current_phase = record.current_phase or "init"
        question_count = (record.question_count or 0) + 1
        event_count = record.event_count or 0
        detail_phase = record.detail_phase or ""
        
        user_answer_lower = user_answer.lower()
        no_experience_keywords = ["没有", "没做过", "没经历", "不太记得", "回忆不起来", "记不清", "没有这种情况", "没遇到过"]
        has_no_experience_keyword = any(kw in user_answer_lower for kw in no_experience_keywords)
        
        next_question, next_phase, next_event_count, next_detail_phase = "", current_phase, event_count, detail_phase
        
        behavior_events = record.behavior_events or []
        last_behavior = behavior_events[-1] if behavior_events else None
        evaluation = last_behavior.get("evaluation") if last_behavior else None
        
        has_experience_value = evaluation.get("has_experience", {}).get("value") if evaluation else None
        match_competency_value = evaluation.get("match_competency", {}).get("value") if evaluation else None
        
        has_no_experience = has_experience_value == False
        
        should_switch_example = has_no_experience or (match_competency_value == False)
        
        used_indices = record.used_question_indices or []
        competency_questions = current_competency.get("questions", [])
        
        next_question = await self._generate_followup_question(
            current_competency=current_competency,
            current_phase=current_phase,
            behavior_event=last_behavior.get("extracted") if last_behavior else None,
            evaluation=evaluation,
            messages=messages,
            event_count=event_count,
            used_question_indices=used_indices,
            questions=competency_questions,
            force_new_example=should_switch_example
        )
        
        if next_question == "__TERMINATE__":
            next_phase = "terminate"
            next_question = "感谢分享，这个胜任力的访谈已完成。"
            should_terminate = True
            record.is_completed = True
        elif next_question:
            if should_switch_example:
                event_count += 1
                next_event_count = event_count
                available_indices = [i for i in range(len(competency_questions)) if i not in used_indices]
                if not available_indices:
                    next_phase = "terminate"
                    next_question = "感谢分享，这个胜任力的访谈已完成。"
                    should_terminate = True
                    record.is_completed = True
                else:
                    next_phase = "init"
            else:
                if current_phase == "init":
                    next_phase = "background"
                elif current_phase == "background":
                    next_phase = "match_check"
                elif current_phase == "match_check":
                    next_phase = "detail"
                    next_detail_phase = "thinking"
                elif current_phase == "detail":
                    if detail_phase == "thinking":
                        next_detail_phase = "action"
                    elif detail_phase == "action":
                        next_detail_phase = "result"
                    elif detail_phase == "result":
                        next_detail_phase = "reflection"
                    elif detail_phase == "reflection":
                        next_phase = "terminate"
        else:
            if current_phase == "init":
                if should_switch_example:
                    available_indices = [i for i in range(len(competency_questions)) if i not in used_indices]
                    if available_indices:
                        next_question = competency_questions[available_indices[0]]
                        used_indices.append(available_indices[0])
                    else:
                        next_phase = "terminate"
                        next_question = "感谢分享，这个胜任力的访谈已完成。"
                        should_terminate = True
                        record.is_completed = True
                    event_count += 1
                    next_event_count = event_count
                else:
                    next_phase = "background"
                    next_question = "请详细描述一下当时是什么情况？您在其中担任什么角色？"
            elif current_phase == "background":
                next_phase = "match_check"
                next_question = "当时您面临的最大挑战或困难是什么？"
            elif current_phase == "match_check":
                if should_switch_example:
                    event_count += 1
                    available_indices = [i for i in range(len(competency_questions)) if i not in used_indices]
                    if available_indices:
                        next_question = competency_questions[available_indices[0]]
                        used_indices.append(available_indices[0])
                        next_phase = "init"
                    else:
                        next_phase = "terminate"
                        next_question = "感谢分享，这个胜任力的访谈已完成。"
                        should_terminate = True
                        record.is_completed = True
                    next_event_count = event_count
                else:
                    next_phase = "detail"
                    next_detail_phase = "thinking"
                    next_question = "面对这个问题，您当时是怎么考虑的？"
            elif current_phase == "detail":
                if detail_phase == "thinking":
                    next_detail_phase = "action"
                    next_question = "您具体是怎么做的？采取了哪些行动？"
                elif detail_phase == "action":
                    next_detail_phase = "result"
                    next_question = "最后的结果怎么样？"
                elif detail_phase == "result":
                    next_detail_phase = "reflection"
                    next_question = "事后您有什么总结或反思？这段经历给您带来了什么？"
                else:
                    next_phase = "terminate"
                    next_question = "感谢分享，这个胜任力的访谈已完成。"
        
        record.current_phase = next_phase
        record.question_count = question_count
        record.event_count = next_event_count
        record.detail_phase = next_detail_phase
        
        should_terminate = False
        if next_phase == "terminate":
            should_terminate = True
            record.is_completed = True
        elif question_count >= 20:
            should_terminate = True
            record.is_completed = True
            next_question = "提问数量已达上限，感谢您的参与！"
        
        if next_question:
            messages.append({"role": "ai", "content": next_question, "timestamp": datetime.utcnow().isoformat()})
            
            if should_switch_example and questions and used_indices is not None:
                for i, q in enumerate(questions):
                    if q == next_question and i not in used_indices:
                        used_indices.append(i)
                        record.used_question_indices = used_indices
                        break
        
        record.messages = messages
        await db.commit()
        
        competency_info = current_competency if current_competency else {}
        await self._extract_behavior_event(messages, record, competency_info)
        
        if should_terminate:
            if current_index + 1 >= len(competencies):
                session.status = "completed"
                await db.commit()
                return {
                    "next_action": "finish",
                    "ai_message": {"content": "恭喜您已完成所有胜任力的行为事件访谈练习！", "type": "completion"},
                    "progress": {"current": len(competencies), "total": len(competencies)}
                }
            else:
                session.current_competency_index = current_index + 1
                next_comp = competencies[current_index + 1]
                next_question = next_comp.get("questions", ["请分享"])[0]
                
                next_record = CompetencyRecord(
                    session_id=session_id,
                    competency_name=next_comp["name"],
                    competency_index=current_index + 1,
                    messages=[{"role": "ai", "content": next_question, "timestamp": datetime.utcnow().isoformat()}],
                    behavior_events=[],
                    is_completed=False,
                    current_phase="init",
                    question_count=0,
                    event_count=0,
                    used_question_indices=[0]
                )
                db.add(next_record)
                await db.commit()
                
                return {
                    "next_action": "next_competency",
                    "ai_message": {"content": next_question, "type": "transition"},
                    "progress": {"current": current_index + 2, "total": len(competencies)}
                }
        
        return {
            "next_action": "continue",
            "ai_message": {"content": next_question, "type": "question"},
            "progress": {"current": current_index + 1, "total": len(competencies)}
        }
    
    async def get_session_status(
        self,
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        session = await db.get(PracticeSession, session_id)
        if not session:
            raise ValueError("会话不存在")
        
        # 解析questionnaire_content（支持新格式JSON、旧格式JSON和文本）
        questionnaire_content = parse_questionnaire_content(
            session.questionnaire_content if isinstance(session.questionnaire_content, str) else json.dumps(session.questionnaire_content)
        )
        competencies = questionnaire_content.get("competencies", [])
        
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
    
    async def _extract_behavior_event(
        self,
        messages: List[Dict],
        record: CompetencyRecord,
        competency_info: Dict[str, Any] = None
    ) -> None:
        """从对话中提取行为事件关键信息"""
        if len(messages) < 4:
            return
        
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        if not user_messages:
            return
        
        conversation = "\n".join([
            f"用户: {msg}" for msg in user_messages
        ])
        
        try:
            extract_prompt = ChatPromptTemplate.from_template(BEHAVIOR_EXTRACT_PROMPT)
            extract_chain = extract_prompt | self.llm | StrOutputParser()
            response = await extract_chain.ainvoke({"conversation": conversation})
            
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            behavior_event = json.loads(response.strip())
            
            evaluation = {"match_competency": None, "detail_sufficient": None, "logic_right": None}
            if competency_info:
                eval_prompt = ChatPromptTemplate.from_template(BEHAVIOR_EVALUATE_PROMPT)
                eval_chain = eval_prompt | self.llm | StrOutputParser()
                eval_response = await eval_chain.ainvoke({
                    "competency_name": competency_info.get("name", ""),
                    "competency_meaning": competency_info.get("meaning", ""),
                    "behavior_criteria": competency_info.get("criteria", ""),
                    "conversation": conversation,
                    "behavior_event": json.dumps(behavior_event, ensure_ascii=False)
                })
                
                eval_response = eval_response.strip()
                if eval_response.startswith("```json"):
                    eval_response = eval_response[7:]
                if eval_response.startswith("```"):
                    eval_response = eval_response[3:]
                if eval_response.endswith("```"):
                    eval_response = eval_response[:-3]
                
                evaluation = json.loads(eval_response.strip())
            
            behavior_events = record.behavior_events or []
            behavior_events.append({
                "timestamp": datetime.utcnow().isoformat(),
                "extracted": behavior_event,
                "evaluation": evaluation
            })
            record.behavior_events = behavior_events
            
        except Exception as e:
            logger.error(f"提取行为事件失败: {e}")
    
    async def _generate_followup_question(
        self,
        current_competency: Dict[str, Any],
        current_phase: str,
        behavior_event: Dict[str, Any] = None,
        evaluation: Dict[str, Any] = None,
        messages: List[Dict] = None,
        event_count: int = 0,
        used_question_indices: List[int] = None,
        questions: List[str] = None,
        force_new_example: bool = False
    ) -> str:
        """通过大模型生成追问问题"""
        user_answer_lower = ""
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_answer_lower = msg.get("content", "").lower()
                    break
        
        no_experience_keywords = ["没有", "没做过", "没经历", "不太记得", "回忆不起来", "记不清", "没有这种情况", "没遇到过"]
        has_no_experience = any(kw in user_answer_lower for kw in no_experience_keywords)
        
        match_competency_false = evaluation and evaluation.get("match_competency", {}).get("value") == False
        
        should_switch_example = has_no_experience or match_competency_false
        
        if should_switch_example:
            if questions and used_question_indices is not None:
                available_indices = [i for i in range(len(questions)) if i not in used_question_indices]
                if available_indices:
                    next_idx = available_indices[0]
                    return questions[next_idx]
                else:
                    return "__TERMINATE__"
            
            return "请分享一个您相关的经历可以吗？"
        
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        conversation = "\n".join([
            f"用户: {msg}" for msg in user_messages
        ])
        
        prompt = ChatPromptTemplate.from_template(FOLLOWUP_QUESTION_PROMPT)
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            response = await chain.ainvoke({
                "competency_name": current_competency.get("name", ""),
                "competency_meaning": current_competency.get("meaning", ""),
                "behavior_criteria": json.dumps(current_competency.get("behavior_criteria", []), ensure_ascii=False),
                "current_phase": current_phase,
                "behavior_event": json.dumps(behavior_event, ensure_ascii=False) if behavior_event else "无",
                "evaluation": json.dumps(evaluation, ensure_ascii=False) if evaluation else "无",
                "conversation": conversation
            })
            
            question = response.strip()
            question = question.lstrip("问题：").lstrip("追问：").lstrip("Q:").strip()
            
            if question and len(question) > 3:
                return question
            
        except Exception as e:
            logger.error(f"生成追问问题失败: {e}")
        
        return ""