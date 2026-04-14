from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from src.schemas.questionnaire_schema import QuestionnaireSchema, QuestionnaireMeta, QuestionnaireContent

CASE_CHALLENGE_DESIGN_PROMPT = """你是一个人才评估专家，请基于考察的能力设计案例分析中的关键挑战点。

## 考察能力
{abilities}

## 输出要求
1. 针对每个能力设计1-2个挑战点
2. 挑战点应体现真实商业决策中的复杂性和不确定性"""

CASE_ENTERPRISE_ANALYSIS_PROMPT = """你是一个企业问题诊断专家，请分析以下背景材料，提取关键的企业问题和挑战。

背景材料：
{background_material}

请提取3-5条企业当前面临的核心问题"""

CASE_BOOK_GENERATION_PROMPT = """你是一个命题专家，请基于以下信息生成案例分析题本。

# 考察能力
{abilities}

# 企业背景
{background_material}

# 用户要求
{requirement}

# 题本要求

一、 指导语

二、 案例背景
- 企业概况
- 行业环境
- 面临的主要问题或决策挑战

三、 分析任务
设计2-3个递进式分析任务，引导候选人深入分析问题

四、 思考框架提示（可选）

五、 评分要点（每个能力维度）"""


class CaseWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        background_file_content: Optional[str] = None,
        requirement: str = ""
    ) -> str:
        dimensions = competency_model.get("dimensions", [])
        abilities = "\n".join([
            f"- {d.get('name', '')}: {d.get('description', '')}"
            for d in dimensions
        ])
        
        background_material = background_file_content or "基于通用商业情境"
        
        book_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=CASE_BOOK_GENERATION_PROMPT.format(
                abilities=abilities,
                background_material=background_material,
                requirement=requirement
            )),
            HumanMessage(content="请生成案例分析题本")
        ])
        
        response = await (book_prompt | self.llm).ainvoke({})
        
        # 构建统一JSON格式
        meta = QuestionnaireMeta(
            tool_id="case",
            tool_name="案例分析",
            level=competency_model.get("level"),
            duration=90,
            generated_at=datetime.now().isoformat()
        )
        
        content = QuestionnaireContent(
            scenario=response.content[:500] if response.content else "案例分析场景"
        )
        
        schema = QuestionnaireSchema(meta=meta, content=content)
        return schema.to_json_string()
