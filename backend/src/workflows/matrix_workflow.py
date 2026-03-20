from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import json

MATRIX_SYSTEM_PROMPT = """你是一位人才评估专家，擅长设计评估矩阵。
根据胜任力模型和测评工具，生成最优的评估矩阵配对。
输出格式为JSON，包含matrix字段，格式为：{dimension_name: {tool_id: true/false}}"""

MATRIX_HUMAN_PROMPT = """胜任力模型：{competency_model}

测评工具：{tools}

请为每个能力维度选择最适合的测评工具，生成评估矩阵。
规则：
- 每个能力维度至少选择1-2个工具
- 选择最能评估该能力维度的工具组合
- 考虑工具之间的互补性"""

TOOLS = [
    {"id": "beh", "name": "BEI行为事件访谈"},
    {"id": "lgd", "name": "无领导小组讨论"},
    {"id": "roleplay", "name": "角色扮演"},
    {"id": "case", "name": "案例分析"},
    {"id": "vision", "name": "个人愿景"}
]

class MatrixWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        tools = tools or TOOLS
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=MATRIX_SYSTEM_PROMPT),
            HumanMessage(content=MATRIX_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                tools=str([t["name"] for t in tools])
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content)
        return result
