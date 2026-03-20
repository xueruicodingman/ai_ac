from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

HANDBOOK_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长编写评委手册。
根据已生成的5种测评题本，生成完整的评委手册。
手册应包含：
1. 测评说明（每个环节的目的、时长、评估重点）
2. 评分标准（每个能力维度的5级评分标准）
3. 注意事项（评委须知、行为记录要求等）
4. 行为记录表模板

输出格式为Markdown"""

HANDBOOK_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵：
{matrix}

题本内容：
{questionnaires}

请生成完整的评委手册"""

class HandbookWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        questionnaires: List[Dict[str, str]]
    ) -> str:
        qa_content = "\n\n".join([
            f"【{q.get('tool_id', 'Unknown')} - {q.get('tool_name', '')}】\n{q.get('content', '')}"
            for q in questionnaires
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=HANDBOOK_SYSTEM_PROMPT),
            HumanMessage(content=HANDBOOK_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix),
                questionnaires=qa_content
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
