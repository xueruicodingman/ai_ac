from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class QuestionnaireMeta(BaseModel):
    """题本元信息"""
    tool_id: str  # beh, roleplay, lgd, case, vision
    tool_name: str
    level: Optional[str] = None  # 基层经理/中层经理/高层经理
    duration: Optional[int] = None  # 分钟
    generated_at: Optional[str] = None


class RoleInfo(BaseModel):
    """角色设定（角色扮演用）"""
    subordinate_name: Optional[str] = None
    position: Optional[str] = None
    background: Optional[str] = None
    personality: Optional[str] = None


class CompetencyItem(BaseModel):
    """胜任力条目（BEI用）"""
    name: str
    meaning: Optional[str] = None
    behavior_criteria: Optional[List[Dict[str, Any]]] = None
    challenges: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    followup_rules: Optional[str] = None


class QuestionnaireContent(BaseModel):
    """题本内容主体"""
    role_info: Optional[RoleInfo] = None
    scenario: Optional[str] = None
    competencies: Optional[List[CompetencyItem]] = None
    challenge_points: Optional[List[str]] = None
    company_info: Optional[str] = None
    background: Optional[str] = None
    theory: Optional[str] = None
    followup_strategy: Optional[str] = None
    # 其他工具特定字段
    materials: Optional[List[str]] = None  # 案例分析材料
    discussion_topic: Optional[str] = None  # LGD讨论主题
    vision_prompt: Optional[str] = None  # 个人愿景Prompt


class QuestionnaireSchema(BaseModel):
    """统一题本格式"""
    meta: QuestionnaireMeta
    content: QuestionnaireContent
    
    def to_json_string(self) -> str:
        return self.model_dump_json(ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json_string(cls, json_str: str) -> "QuestionnaireSchema":
        return cls.model_validate_json(json_str)