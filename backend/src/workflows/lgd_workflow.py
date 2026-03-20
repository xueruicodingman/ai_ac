from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

LGD_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长设计无领导小组讨论（LGD）题本。
根据胜任力模型和评估矩阵，生成专业的LGD题本。
题本应包含：
1. 指导语（任务说明、时间安排）
2. 讨论背景材料
3. 讨论任务
4. 评分要点（每个能力维度）

输出格式为Markdown"""

LGD_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵（LGD相关部分）：
{matrix}

要求：
- 设计一个适合6-8人小组讨论的场景
- 背景材料应具有争议性或决策性
- 明确时间分配
- 评分要点清晰"""

class LGDWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any]
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=LGD_SYSTEM_PROMPT),
            HumanMessage(content=LGD_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix.get("matrix", {}))
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
