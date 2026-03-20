from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import json

FEEDBACK_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长撰写反馈版报告。
根据被测者的测评数据，生成专业的反馈报告。

报告结构：
1. 一句话评价
2. 优势项（能力名称、评价语、行为表现）
3. 不足项（能力名称、评价语、行为表现）

要求：
- 语言专业、客观
- 基于具体数据和行为
- 优势与不足都要有行为证据支持
- 输出JSON格式"""

FEEDBACK_HUMAN_PROMPT = """被测者姓名：{name}
得分数据：{scores}
行为记录：{behaviors}

请生成反馈版报告。"""

ORG_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长撰写组织版报告。
根据被测者的测评数据和反馈版报告，生成组织版报告。

报告结构：
1. 个人评价（一句话总结）
2. 个人优势
3. 个人不足
4. 价值观/发展潜力
5. 培养使用建议（含使用建议、风险提示）

要求：
- 语言专业、详细
- 包含具体的培养建议
- 风险提示要客观
- 输出JSON格式"""

ORG_HUMAN_PROMPT = """被测者姓名：{name}
得分数据：{scores}
反馈版报告内容：{feedback_content}

请生成组织版报告。"""

PERSONAL_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长撰写个人版报告。
根据被测者的测评数据，生成个人版报告。

报告结构：
1. 开头段落（先扬后抑式评价）
2. 【优势项】（标注分数情况，如"最高分项、超过5.5分项"）
3. 【待提升项】（标注分数情况，如"低于5分项"）
4. 【发展建议】（3点编号列表）
5. 【课程学习】（课程名、公司/平台、季度年份）
6. 【书籍阅读】（书名列表）

要求：
- 语言温和、鼓励性
- 优势项和待提升项都要标注具体分数
- 发展建议具体可行
- 输出JSON格式"""

PERSONAL_HUMAN_PROMPT = """被测者姓名：{name}
得分数据：{scores}
组织版报告内容：{org_content}

请生成个人版报告。"""

class ReportWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    def _parse_json(self, response: str) -> dict:
        content = response.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content)
    
    async def generate_feedback_report(
        self,
        name: str,
        scores: Dict[str, float],
        behaviors: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=FEEDBACK_SYSTEM_PROMPT),
            HumanMessage(content=FEEDBACK_HUMAN_PROMPT.format(
                name=name,
                scores=scores,
                behaviors=behaviors
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return self._parse_json(response.content)
    
    async def generate_org_report(
        self,
        name: str,
        scores: Dict[str, float],
        feedback_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ORG_SYSTEM_PROMPT),
            HumanMessage(content=ORG_HUMAN_PROMPT.format(
                name=name,
                scores=scores,
                feedback_content=feedback_content
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return self._parse_json(response.content)
    
    async def generate_personal_report(
        self,
        name: str,
        scores: Dict[str, float],
        org_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=PERSONAL_SYSTEM_PROMPT),
            HumanMessage(content=PERSONAL_HUMAN_PROMPT.format(
                name=name,
                scores=scores,
                org_content=org_content
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return self._parse_json(response.content)
