from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

VISION_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长设计个人愿景题本。
根据胜任力模型和评估矩阵，生成专业的个人愿景题本。
题本应包含：
1. 指导语
2. 问题列表（职业目标、成长路径等）
3. 价值观探索问题
4. 评分要点

输出格式为Markdown"""

VISION_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵（个人愿景相关部分）：
{matrix}

要求：
- 问题应引导自我反思
- 探索职业发展规划
- 考察价值观和事业心
- 评分要点关注目标清晰度和行动力"""

class VisionWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any]
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=VISION_SYSTEM_PROMPT),
            HumanMessage(content=VISION_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix.get("matrix", {}))
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
