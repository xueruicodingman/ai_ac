from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

BEH_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长设计BEI行为事件访谈题本。
根据胜任力模型和评估矩阵，生成专业的BEI题本。
题本应包含：
1. 指导语
2. 开场提问
3. 每个能力维度的追问问题（使用STAR法则）
4. 结束语

输出格式为Markdown"""

BEI_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵（BEI相关部分）：
{matrix}

要求：
- 为每个能力维度设计3-5个行为事件访谈问题
- 问题应引导被测者描述具体事例
- 使用STAR法则（情境、任务、行动、结果）
- 语言专业、清晰"""

class BEHWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any]
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=BEH_SYSTEM_PROMPT),
            HumanMessage(content=BEI_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix.get("matrix", {}))
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
