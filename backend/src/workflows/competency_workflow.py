from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import uuid

COMPETENCY_SYSTEM_PROMPT = """你是一位资深的人才评估专家，擅长构建胜任力模型。
根据提供的背景材料和要求，生成专业的胜任力模型。
输出格式为JSON，包含以下字段：
- dimensions: 能力维度数组
  - name: 能力名称
  - meaning: 能力含义
  - behavior_criteria: 行为标准数组
    - title: 行为标准标题
    - description: 行为标准描述"""

COMPETENCY_HUMAN_PROMPT = """请根据以下信息生成胜任力模型：

背景材料：{background}
指定能力：{specified_abilities}
能力数量：{num_competencies}

请生成一个专业的胜任力模型，包含{dimensions_count}个能力维度。"""

class CompetencyWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        background: str = "",
        specified_abilities: List[str] = None,
        num_competencies: int = 5
    ) -> Dict[str, Any]:
        specified = ", ".join(specified_abilities) if specified_abilities else "无"
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=COMPETENCY_SYSTEM_PROMPT),
            HumanMessage(content=COMPETENCY_HUMAN_PROMPT.format(
                background=background or "无",
                specified_abilities=specified,
                num_competencies=num_competencies,
                dimensions_count=num_competencies
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        
        import json
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content)
        for dim in result.get("dimensions", []):
            dim["id"] = str(uuid.uuid4())
            for bc in dim.get("behavior_criteria", []):
                bc["id"] = str(uuid.uuid4())
        
        return result
