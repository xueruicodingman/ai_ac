from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

CASE_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长设计案例分析题本。
根据胜任力模型和评估矩阵，生成专业的案例分析题本。
题本应包含：
1. 指导语
2. 案例背景
3. 分析任务
4. 思考框架提示
5. 评分要点

输出格式为Markdown"""

CASE_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵（案例分析相关部分）：
{matrix}

要求：
- 案例应具有复杂性和多维度
- 包含足够的背景信息
- 允许有多个合理的解决方案
- 评分要点考察分析深度和决策质量"""

class CaseWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any]
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=CASE_SYSTEM_PROMPT),
            HumanMessage(content=CASE_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix.get("matrix", {}))
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
