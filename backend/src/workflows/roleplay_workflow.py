from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

ROLEPLAY_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长设计角色扮演题本。
根据胜任力模型和评估矩阵，生成专业的角色扮演题本。
题本应包含：
1. 指导语
2. 场景描述
3. 被测者角色
4. 对方角色信息
5. 模拟对话引导
6. 评分要点

输出格式为Markdown"""

ROLEPLAY_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵（角色扮演相关部分）：
{matrix}

要求：
- 场景应贴近实际工作情境
- 角色设定清晰
- 给被测者足够的发挥空间
- 评分要点与能力维度对应"""

class RolePlayWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any]
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_SYSTEM_PROMPT),
            HumanMessage(content=ROLEPLAY_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix.get("matrix", {}))
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
