from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

COMPETENCY_SYSTEM_PROMPT = """你现在是一名资深人才测评与干部考察领域的专家，擅长将抽象的胜任力名称转化为可落地、可观察的能力定义和行为标准。

胜任力词条输入示例如下：
问题解决、沟通协作等词语

生成对应的内容：
能力含义：用简洁、专业的语言，清晰界定该胜任力的核心内涵，说明该能力是指在工作场景中，个体具备的何种特质、思维模式或行为倾向，需贴合干部考察、人才测评的实际应用场景。

3 条行为标准：
每条行为标准需包含核心行为维度 + 具体场景行为描述，维度要相互独立、覆盖能力的关键方面，不重复、不交叉。
行为描述必须是【一个概括性的词语：详细的解释】格式，要具备可观察性、可评估性，避免空泛表述，需明确 "在什么场景下，做什么事，达到什么效果"。

严格参考以下示例的结构和风格撰写：
解决问题能力
面对各类复杂工作问题时，能够运用科学的思维方式、方法和技能，有效分析问题、制定解决方案并推动方案落地实施，从而达成预期目标的特质和行为倾向。
1. 问题拆解与根源分析：面对复杂问题时，能将其拆解为若干具体、可落地的子问题，通过收集数据、调研访谈等方式定位问题根源，而非仅处理表面现象。
2. 方案设计与择优落地：基于问题分析提出至少 2 种可行解决方案，结合成本、风险、效果等维度评估对比，选择最优方案并制定清晰的执行步骤，跟进落地进度。
3. 复盘优化与经验沉淀：问题解决后，及时复盘整个过程中的成功经验与不足，总结可复用的方法或规避措施，形成案例沉淀，为同类问题提供参考。

请你根据上述规则，针对我给出的胜任力词条，输出能力含义和3 条行为标准，无需额外内容。
输出格式为JSON：
{
  "competency_name": "词条名称",
  "meaning": "能力含义",
  "behavior_criteria": [
    {"title": "维度1", "description": "详细描述"},
    {"title": "维度2", "description": "详细描述"},
    {"title": "维度3", "description": "详细描述"}
  ]
}"""

COMPETENCY_HUMAN_PROMPT = "我提供的胜任力词条是：{competency_name}"


class CompetencyGenWorkflow:
    """生成胜任力模型的工作流（Coze workflow转换）"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser()
    
    async def generate(
        self,
        competency_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        批量生成胜任力定义
        
        Args:
            competency_names: 胜任力词条列表，如 ["问题解决", "沟通协作"]
        
        Returns:
            每个词条的胜任力定义
        """
        results = []
        
        for name in competency_names:
            result = await self._generate_single(name)
            results.append(result)
        
        return results
    
    async def _generate_single(self, competency_name: str) -> Dict[str, Any]:
        """生成单个胜任力定义"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=COMPETENCY_SYSTEM_PROMPT),
            HumanMessage(content=COMPETENCY_HUMAN_PROMPT.format(competency_name=competency_name))
        ])
        
        chain = prompt | self.llm | self.parser
        response = await chain.ainvoke({})
        
        # 确保返回格式正确
        return {
            "name": competency_name,
            "meaning": response.get("meaning", ""),
            "behavior_criteria": response.get("behavior_criteria", [])
        }


# 使用示例（在后端service中调用）
"""
from src.services.ai_service import AIService

class CompetencyService(AIService):
    async def generate_from_workflow(
        self,
        competency_names: List[str]
    ) -> List[Dict[str, Any]]:
        workflow = CompetencyGenWorkflow(self.llm)
        return await workflow.generate(competency_names)
"""