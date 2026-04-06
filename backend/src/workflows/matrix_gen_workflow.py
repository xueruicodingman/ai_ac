from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

MATRIX_SYSTEM_PROMPT = """你是一个人才评估专家，你将会接收到一个胜任力维度，其中包括能力名称，能力含义，能力标准。

你需要结合能力的含义和行为标准，为其匹配合适的考察工具，可选的考察工具包括：行为面试、无领导小组讨论、角色扮演、个人愿景、商业案例。

输出示例如下：
[沟通能力]：无领导小组讨论，角色扮演

注意：输出中不需要包含理由、解释等其他内容

各类工具的考场方式和考察能力类型说明如下：

1. 行为面试
考察方式：基于 "过去的行为是未来行为的最佳预测" 这一核心，面试官通过提问，让候选人回忆并描述过往真实工作或生活中的具体经历、行为细节。常用提问句式为 "请举例说明你在 XX 情况下是如何做的"，会深挖 "情境（S）— 任务（T）— 行动（A）— 结果（R）" 四个要素。
适合考察的能力：责任心、沟通协调能力、问题解决能力、抗压能力、团队协作能力、执行力等通用软能力，也可考察与岗位相关的专项技能应用经验。

2. 无领导小组讨论
考察方式：将候选人分为小组，给出一个开放性问题或任务（如方案设计、资源分配、争议决策等），不指定领导者，让小组成员在规定时间内自主讨论并达成一致结论。面试官全程观察候选人的发言、互动、组织等表现。
适合考察的能力：领导力、团队协作能力、逻辑思维能力、沟通表达能力、应变能力、冲突解决能力，以及在压力下的分析和决策能力。

3. 角色扮演
考察方式：设定与岗位工作高度相关的真实场景（如客户投诉处理、跨部门协作谈判、下属绩效沟通等），指定候选人扮演特定角色，与面试官或工作人员扮演的角色进行互动，完成既定任务目标。面试官根据候选人的应对方式、言行举止进行评估。
适合考察的能力：岗位实操能力、沟通谈判能力、情绪管理能力、问题解决能力、服务意识（如客服岗位）、危机处理能力，以及对岗位场景的快速适应能力。

4. 个人愿景
考察方式：通过书面撰写、口头陈述或结构化问答的形式，让候选人阐述自己的职业规划、人生目标、价值观追求，以及个人愿景与组织发展目标的契合度。面试官重点关注愿景的清晰度、可行性、稳定性，以及候选人的自我认知和驱动力。
适合考察的能力：自我认知能力、职业规划能力、目标驱动力、价值观匹配度、学习成长意愿，以及对组织的认同感和忠诚度。

5. 商业案例
考察方式：提供一份真实或模拟的商业案例（如企业市场拓展困境、利润下滑问题、新产品上线策略等），要求候选人在规定时间内进行数据分析、问题诊断、方案设计，并向面试官展示和答辩。面试官关注分析的逻辑性、方案的可行性和创新性。
适合考察的能力：商业分析能力、逻辑思维能力、数据处理能力、战略规划能力、创新能力、口头汇报能力，以及针对商业问题的综合决策能力，适合管理岗、咨询岗、市场岗等岗位的考察。

请为输入的胜任力维度推荐合适的考察工具，输出格式：[能力名称]：工具1，工具2"""

TOOL_MAPPING = {
    "beh": "行为面试",
    "lgd": "无领导小组讨论",
    "roleplay": "角色扮演",
    "vision": "个人愿景",
    "case": "商业案例"
}

TOOL_MAPPING_CN_TO_ID = {
    "行为面试": "beh",
    "无领导小组讨论": "lgd",
    "角色扮演": "roleplay",
    "个人愿景": "vision",
    "商业案例": "case"
}


class MatrixGenWorkflow:
    """生成评估矩阵的工作流（Coze workflow转换）"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = StrOutputParser()

    async def generate(
        self,
        dimensions: List[Dict[str, Any]],
        selected_tools: List[str] = None
    ) -> Dict[str, Any]:
        """
        为每个胜任力维度匹配合适的测评工具
        
        Args:
            dimensions: 胜任力维度列表，每个包含 name, meaning, behavior_criteria
            selected_tools: 用户选中的工具ID列表
        
        Returns:
            {dimension_name: [tool_id1, tool_id2, ...]}
        """
        print(f"[MATRIX WORKFLOW] Starting generation for {len(dimensions)} dimensions")
        print(f"[MATRIX WORKFLOW] Selected tools: {selected_tools}")
        
        # 构建可用工具列表
        available_tools = []
        if selected_tools:
            for tool_id in selected_tools:
                tool_name = TOOL_MAPPING.get(tool_id, tool_id)
                available_tools.append(f"{tool_id}:{tool_name}")
        else:
            available_tools = [f"{k}:{v}" for k, v in TOOL_MAPPING.items()]
        
        print(f"[MATRIX WORKFLOW] Available tools: {available_tools}")
        
        results = {}

        for dim in dimensions:
            name = dim.get("name", "")
            meaning = dim.get("meaning", "")
            behavior_criteria = dim.get("behavior_criteria", [])
            
            print(f"[MATRIX WORKFLOW] Processing: {name}")

            # 构建行为标准文本
            behavior_text = ""
            for i, bc in enumerate(behavior_criteria[:3], 1):
                behavior_text += f"{i}. {bc.get('title', '')}：{bc.get('description', '')}\n"

            # 构造输入，包含可用工具限制
            tools_list = ", ".join([f"【{t}】" for t in available_tools])
            input_text = f"""能力名称：{name}
能力含义：{meaning}
行为标准：
{behavior_text}

请从以下工具中选择最合适的（只能选择这些工具）：{tools_list}"""

            # 调用LLM
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=MATRIX_SYSTEM_PROMPT),
                HumanMessage(content=f"用户输入的胜任力维度为：{input_text}")
            ])

            try:
                chain = prompt | self.llm | self.parser
                response = await chain.ainvoke({})
                print(f"[MATRIX WORKFLOW] LLM response for {name}: {response}")
                
                # 解析LLM返回的工具
                tools = self._parse_tools_response(response, selected_tools)
                print(f"[MATRIX WORKFLOW] Parsed tools for {name}: {tools}")
                
                results[name] = tools
            except Exception as e:
                print(f"[MATRIX WORKFLOW] Error processing {name}: {str(e)}")
                results[name] = []

        print(f"[MATRIX WORKFLOW] Final results: {results}")
        return results

    def _parse_tools_response(self, response: str, selected_tools: List[str] = None) -> List[str]:
        """解析LLM返回的工具字符串，转换为工具ID列表"""
        tools = []
        
        # 格式可能是: [沟通能力]：无领导小组讨论，角色扮演
        # 或者直接是: 无领导小组讨论，角色扮演
        parts = response.replace("[", "").replace("]", "").replace("\n", "").split("：")
        
        tool_text = parts[-1] if len(parts) > 1 else response
        
        # 分割工具名称
        tool_names = [t.strip() for t in tool_text.split("，") if t.strip()]
        
        for tool_name in tool_names:
            tool_id = TOOL_MAPPING_CN_TO_ID.get(tool_name)
            if tool_id and tool_id not in tools:
                # 如果用户指定了工具列表，只返回在列表中的工具
                if selected_tools is None or tool_id in selected_tools:
                    tools.append(tool_id)
        
        return tools


# 使用示例（在后端service中调用）
"""
from src.services.ai_service import AIService

class MatrixService(AIService):
    async def generate_from_workflow(
        self,
        dimensions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        workflow = MatrixGenWorkflow(self.llm)
        return await workflow.generate(dimensions)
"""