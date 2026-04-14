from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from datetime import datetime
import json

from src.schemas.questionnaire_schema import QuestionnaireSchema, QuestionnaireMeta, QuestionnaireContent, CompetencyItem

BEI_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长设计BEI行为事件访谈题本。"""

BEI_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵（BEI相关部分）：
{matrix}

要求：
- 为每个能力维度设计3-5个行为事件访谈问题
- 问题应引导被测者描述具体事例
- 使用STAR法则（情境、任务、行动、结果）
- 语言专业、清晰"""

CHALLENGE_SYSTEM_PROMPT = """你是一个命题专家，请你基于胜任力模型的内涵，来分析能够考察该胜任力的核心任务挑战。

# 输入内容
能力名称：{ability_name}
能力含义：{ability_meaning}
关键行为：
{behavior_criteria}

# 输出原则
针对输入的能力及其内涵输出1-3个核心任务挑战，候选人应对这些挑战时候的表现是完全不同的。

核心任务挑战必须满足以下三个条件：
- 瓶颈性：不解决它，任务整体进度卡壳，其他工作做了也白做 / 效果极有限。
- 必要性：它是必须解决的，不是可选优化；没有它，目标就不成立。
- 影响面：它会牵一发动全身：影响方案设计、资源投入、最终结果质量。

核心挑战需要具体到场景一些，但是不要与某个岗位强相关，需要是每个岗位都可能遇到的。

# 输出要求
分条目输出核心挑战，每一条不能超过30字。

# 输出示例
· 工作推进遇多方分歧阻碍，需协调达成一致并保障进度
· 既定计划遇突发状况，需快速调整并确保目标完成"""

QUESTION_SYSTEM_PROMPT = """你是一个行为事件访谈命题专家，请你帮我完成命题。

# 输入内容
你的输入为：
胜任力：{ability}
能力含义：{ability_meaning}
关键行为：{behavior_criteria}
核心挑战：{challenges}

# 输出原则
你将会得到的输入是关于胜任力条目和能够考察该胜任力的核心挑战。你需要基于此来针对每一个核心挑战生成行为事件的引导性提问。不需要生成后续对应的追问问题，只需要1个话题引导性的问题。引导性提问要求如下：
1. 每个引导性提问不要超过40字
2. 每个引导性提问只提一个问题，不能是连续地提问
输出内容：包括胜任力、核心挑战、引导提问，每个引导性提问不要超过50字；

# 输出格式
【{ability}】
1. 能力含义
{ability_meaning}
2. 关键行为
{behavior_criteria}
3. 核心挑战
{challenges}
4. 引导提问
· 问题1
· 问题2
· 问题3"""

THEORY_SYSTEM_PROMPT = """你是一个行为面试专家，你需要撰写一份行为面试原理的说明。主要内容包括：理论假设、操作方法、注意事项。

# 输出要求
理论假设：50字以内。
操作方法：分条目，累计150字以内；
注意事项：分条目，累计200字以内；"""

FOLLOWUP_SYSTEM_PROMPT = """你是一个行为面试专家，你需要撰写一份行为面试追问策略说明。主要内容包括：追问目标、操作方法、注意事项。

# 输出要求
追问目标：50字以内。
操作方法：分条目，累计150字以内；
注意事项：分条目，累计200字以内；"""

INTEGRATION_SYSTEM_PROMPT = """你是一个文档专家，你特别擅长撰写材料。你需要把输出的内容整合成一个文档。其结构如下：
一、 行为面试原理
二、 考察方法与引导提问
三、 追问策略
四、 企业背景信息

# 输出要求
1. 请你处理好标题的等级，请你处理好段落、项目符号等内容;
2. 标题上不好带任何括号之类的符号，要写规范；
3. 尽量满足用户的要求:{requirement}"""

FILE_EXTRACTION_SYSTEM_PROMPT = """请你通过链接访问文件，并且提取文件中的内容，按照良好的格式输出，不要遗漏关键信息，不要做二次解读，还原原文本。"""

FILE_FORMAT_SYSTEM_PROMPT = """你是一个文案整理大师，请你输入的材料整理好一篇完整的材料，要求如下：
1. 行文风格要官方，不要口语化；
2. 段落布局、格式要正确；
3. 字数不要超过2000字；
4. 不要改变原文含义，尽量还原原文；"""


class BEHWorkflow:
    def __init__(self, llm):
        self.llm = llm
        self.parser = StrOutputParser()
        self.json_parser = JsonOutputParser()

    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        background_file_content: Optional[str] = None,
        requirement: str = ""
    ) -> str:
        """生成BEI行为事件访谈题本
        
        Args:
            competency_model: 胜任力模型
            evaluation_matrix: 评估矩阵
            background_file_content: 背景材料内容（可选）
            requirement: 用户要求（可选）
        
        Returns:
            生成的题本内容（JSON格式）
        """
        dimensions = competency_model.get("dimensions", [])
        
        # 1. 生成行为面试原理（保持文本）
        theory_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=THEORY_SYSTEM_PROMPT),
            HumanMessage(content="请生成行为面试原理说明")
        ])
        theory_chain = theory_prompt | self.llm | self.parser
        theory_content = await theory_chain.ainvoke({})
        
        # 2. 生成追问策略（保持文本）
        followup_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=FOLLOWUP_SYSTEM_PROMPT),
            HumanMessage(content="请生成行为面试追问策略说明")
        ])
        followup_chain = followup_prompt | self.llm | self.parser
        followup_content = await followup_chain.ainvoke({})
        
        # 3. 为每个能力维度生成核心挑战和引导提问（直接输出JSON）
        competencies_data = []
        for dim in dimensions:
            ability_name = dim.get("name", "")
            ability_meaning = dim.get("meaning", "")
            behavior_criteria = dim.get("behavior_criteria", [])
            
            # 构建行为标准文本
            behavior_text = ""
            for bc in behavior_criteria[:3]:
                behavior_text += f"- {bc.get('title', '')}: {bc.get('description', '')}\n"
            
            # 3.1 直接生成JSON格式的完整胜任力数据
            competency_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""你是一个行为事件访谈命题专家。请为以下胜任力生成JSON格式的题本数据。

胜任力名称：{ability_name}
能力含义：{ability_meaning}
关键行为标准：
{behavior_text}

请返回以下JSON格式（必须严格是有效JSON，不能有其他文字）：
{{
    "name": "{ability_name}",
    "meaning": "{ability_meaning}",
    "behavior_criteria": [
        {{"title": "行为1标题", "description": "行为1描述"}},
        {{"title": "行为2标题", "description": "行为2描述"}},
        {{"title": "行为3标题", "description": "行为3描述"}}
    ],
    "challenges": ["挑战1", "挑战2", "挑战3"],
    "questions": ["问题1", "问题2", "问题3"],
    "followup_rules": "1. 使用STAR法则（情境、任务、行动、结果）进行追问；2. 切换问题时机：① 已判断该行为与胜任力无关，候选人讲的内容偏离，再问也不会增加有效信息；② 出现明显重复、无新信息，反复绕同一个例子，没有补充新行为、新场景、新做法；③ 候选人明显回忆不起来、情绪不适或过度防御，继续追问只会得到编造内容"
}}"""),
                HumanMessage(content="请直接返回JSON，不要有其他文字")
            ])
            
            try:
                competency_chain = competency_prompt | self.llm | self.json_parser
                competency_data = await competency_chain.ainvoke({})
                competencies_data.append(competency_data)
            except Exception as e:
                # 如果JSON解析失败，使用备用数据
                competencies_data.append({
                    "name": ability_name,
                    "meaning": ability_meaning,
                    "behavior_criteria": [
                        {"title": bc.get("title", ""), "description": bc.get("description", "")}
                        for bc in behavior_criteria[:3]
                    ],
                    "challenges": [f"围绕{ability_name}的核心挑战场景"],
                    "questions": [f"请分享一次关于{ability_name}的具体经历"],
                    "followup_rules": "1. 使用STAR法则（情境、任务、行动、结果）进行追问；2. 切换问题时机：① 已判断该行为与胜任力无关，候选人讲的内容偏离，再问也不会增加有效信息；② 出现明显重复、无新信息，反复绕同一个例子，没有补充新行为、新场景、新做法；③ 候选人明显回忆不起来、情绪不适或过度防御，继续追问只会得到编造内容"
                })
        
        # 4. 构建元信息，输出统一JSON格式
        meta = QuestionnaireMeta(
            tool_id="beh",
            tool_name="BEI行为事件访谈",
            level=competency_model.get("level"),
            duration=60,
            generated_at=datetime.now().isoformat()
        )

        # 转换competencies为CompetencyItem列表
        competency_items = []
        for comp in competencies_data:
            competency_items.append(CompetencyItem(
                name=comp.get("name", ""),
                meaning=comp.get("meaning"),
                behavior_criteria=comp.get("behavior_criteria"),
                challenges=comp.get("challenges"),
                questions=comp.get("questions"),
                followup_rules=comp.get("followup_rules")
            ))

        content = QuestionnaireContent(
            theory=theory_content,
            followup_strategy=followup_content,
            competencies=competency_items,
            background=background_file_content
        )

        schema = QuestionnaireSchema(meta=meta, content=content)
        return schema.to_json_string()
