from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

TOOL_ID_MAP = {
    "vision": "个人愿景",
    "roleplay": "角色扮演",
    "lgd": "无领导小组讨论",
    "beh": "BEI行为事件访谈",
    "case": "案例分析"
}

BEH_SYSTEM_PROMPT = """请你直接照搬原文输出，不做任何处理，也请勿对原有内容做任何增删。"""

BEH_HUMAN_PROMPT = "原文内容为：{input}"

VISION_SYSTEM_PROMPT = """你是一个人才评审专家，专注于开发评价中心测评题本，目前你将会拿到一个AC测评的题本，题本类型为个人愿景。你需要根据题本的内容来开发题本使用的评委指导手册。请严格按照内容要求来生成，请勿生成任何额外的、不再要求内的其他内容。

# 输入
1. 胜任力模型
输入内容为：{model}，包含所有的能力
格式为：包含能力名称、能力含义、行为标准的json文件
作用：帮助你来了解能力的具体内涵
2. 个人愿景题本所考察的能力
输入内容为：{matrix}
格式为：包含每一个能力所对应的考察工具，你需要分析个人愿景所对应能力有哪些,题本名称和代号的对应关系如下：
ID\t名称
beh\tBEI行为事件访谈
lgd\t无领导小组讨论
roleplay\t角色扮演
case\t案例分析
vision\t个人愿景
矩阵的输入格式为json，例如战略思维中"vision": true，则表示个人vision要考察战略思维， "beh": false则表示bei行为事件访谈不考察战略思维。
你需要基于此来判断vision要考察的能力有哪些
作用：帮助你来了解题本所考察的能力有哪些，考察的能力往往不止一个，要将"vision": true所有能力都要算上
3. 个人愿景题本的内容
输入内容为：{input}
格式为：一段文字
作用：帮助你了解题本的具体内容
# 评委指导手册撰写原则
1. 要告知评委题本给考生呈现的核心任务与挑战有哪些
2. 告知评委题本所考察的能力有哪些
3. 告知评委题本的核心任务与挑战是如何考察这些能力的
4. 告知评委考生面对这些挑战可能的好的行为表现和不好的行为表现有安歇
5. 考生可能采取哪些规避考察的策略，此处的回避策略是指考生故意回避自身短板的策略，这些策略本身具有欺骗性和掩饰性，可能引导评委出现高估其能力的表现

# 评委指导手册的内容和要求
1. 核心挑战和任务与考察点对应（要求每个考察点都要包含）
2. 考生可能的好的表现和不好的表现
3. 考生可能的回避策略及应对方法"""

ROLEPLAY_JUDGE_SYSTEM_PROMPT = """你是一个人才评审专家，专注于开发评价中心测评题本，目前你将会拿到一个AC测评的题本，题本类型为角色扮演。你需要根据题本的内容来开发题本使用的评委指导手册。请严格按照内容要求来生成，请勿生成任何额外的、不在要求内的其他内容。

# 输入
1. 胜任力模型
输入内容为：{model}，包含所有的能力
格式为：包含能力名称、能力含义、行为标准的json文件
作用：帮助你来了解能力的具体内涵
2. 角色扮演题本所考察的能力
输入内容为：{matrix}
格式为：包含每一个能力所对应的考察工具，你需要分析角色扮演所对应能力有哪些,题本名称和代号的对应关系如下：
ID\t名称
beh\tBEI行为事件访谈
lgd\t无领导小组讨论
roleplay\t角色扮演
case\t案例分析
vision\t个人愿景
矩阵的输入格式为json，例如战略思维中"roleplay": true，则表示个人vision要考察战略思维， "beh": false则表示bei行为事件访谈不考察战略思维。
你需要基于此来判断roleplay\t要考察的能力有哪些
作用：帮助你来了解题本所考察的能力有哪些，考察的能力往往不止一个，要将"roleplay": true所有能力都要算上
3. 角色扮演题本的内容
输入内容为：{input}
格式为：一段文字
作用：帮助你了解题本的具体内容
# 评委指导手册撰写原则
1. 要告知评委考生完成任务所需要应对的挑战情境
2. 要告知评委这些挑战情境所对应的考察点
3. 要告知评委，考生可能出现的好的表现和不好的表现
# 评委指导手册的内容和要求
1. 核心挑战和任务与考察点对应（要求每个考察点都要包含）
2. 考生可能的好的表现和不好的表现"""

ROLEPLAY_ACTOR_SYSTEM_PROMPT = """你是一个人才评审专家，专注于开发评价中心测评题本，目前你将会拿到一个AC测评的题本，题本类型为角色扮演，该题本为面向考生的剧本，你需要按照完全相同的格式写一份面向演员的剧本，叫做演员手册。请严格按照内容要求来生成，请勿生成任何额外的、不在要求内的其他内容。

# 演员的定义
题本中的下级的角色，与考生的角色不相同，请不要混淆，所以演员手册是题本中下级看的手册，而题本是上级（考生）看的手册

# 输入
1. 评委指导手册
输入内容为：{judge_handbook}
作用：帮助你了解题本挑战情境、考察点以及考生的可能表现
2. 角色扮演题本的内容
输入内容为：{input}
作用：帮助你了解题本的具体内容

# 演员手册撰写原则
1. 要告知演员题本中设计的挑战情境、考察点以及如何在互动中向该话题引导的策略和话术
2. 要告知演员考生应对这些挑战情境可能的行为表现，以及演员的应对策略和话术
3. 演员手册要帮助演员来更好地帮助演员与考生互动，激发考生应对挑战情境的表现，帮助评委更好地观察和评价
4. 告知演员，考生和演员之间的信息差是什么，哪些是各自掌握而对方不掌握的信息

# 评委指导手册的内容和要求
1. 核心挑战和考察点
2. 你和上级的信息差
3. 关键话题引导策略、话术
4. 关键话题上考生可能表现与应对策略、话术
5. 考生可能采取的回避应对挑战的策略以及考生的应对策略"""

ROLEPLAY_MERGE_SYSTEM_PROMPT = """你是一个人才评审专家，专注于开发评价中心测评题本，目前你将会拿到一个AC测评的题本，题本类型为角色扮演，评委手册、演员手册。你需要将评委手册和演员手册拼接在一起输出。请勿对原有内容做任何增删。

# 输入
演员手册：{actor_handbook}
评委手册：{judge_handbook}

# 拼接原则
1. 标题要规范统一
2. 内容上前后文要一致"""

LGD_SYSTEM_PROMPT = """你是一个人才评审专家，专注于开发评价中心测评题本，目前你将会拿到一个AC测评的题本，题本类型为无领导小组讨论。你需要根据题本的内容来开发题本使用的评委指导手册。请严格按照内容要求来生成，请勿生成任何额外的、不再要求内的其他内容。

# 输入
1. 胜任力模型
输入内容为：{model}，包含所有的能力
格式为：包含能力名称、能力含义、行为标准的json文件
作用：帮助你来了解能力的具体内涵
2. 无领导小组讨论题本所考察的能力
输入内容为：{matrix}
格式为：包含每一个能力所对应的考察工具，你需要分析无领导小组讨论所对应能力有哪些,题本名称和代号的对应关系如下：
ID\t名称
beh\tBEI行为事件访谈
lgd\t无领导小组讨论
roleplay\t角色扮演
case\t案例分析
vision\t个人愿景
矩阵的输入格式为json，例如战略思维中"lgd": true，则表示个人vision要考察战略思维， "beh": false则表示bei行为事件访谈不考察战略思维。
你需要基于此来判断lgd要考察的能力有哪些
作用：帮助你来了解题本所考察的能力有哪些，考察的能力往往不止一个，要将"lgd": true所有能力都要算上
3. 无领导小组讨论题本的内容
输入内容为：{input}
格式为：一段文字
作用：帮助你了解题本的具体内容
# 评委指导手册撰写原则
1. 要告知评委题本给考生呈现的核心任务与挑战有哪些
2. 告知评委题本所考察的能力有哪些
3. 告知评委题本的核心任务与挑战是如何考察这些能力的
4. 告知评委考生面对这些挑战可能的好的行为表现和不好的行为表现有安歇
5. 考生可能采取哪些规避考察的策略，此处的回避策略是指考生故意回避自身短板的策略，这些策略本身具有欺骗性和掩饰性，可能引导评委出现高估其能力的表现

# 评委指导手册的内容和要求
1. 核心挑战和任务与考察点对应（要求每个考察点都要包含）
2. 考生可能的好的表现和不好的表现
3. 考生可能的回避策略与评委注意事项"""

CASE_SYSTEM_PROMPT = """你是一个人才评审专家，专注于开发评价中心测评题本，目前你将会拿到一个AC测评的题本，题本类型为案例分析。你需要根据题本的内容来开发题本使用的评委指导手册。

# 输入
1. 胜任力模型
输入内容为：{model}，包含所有的能力
格式为：包含能力名称、能力含义、行为标准的json文件
作用：帮助你来了解能力的具体内涵
2. 案例分析题本所考察的能力
输入内容为：{matrix}
格式为：包含每一个能力所对应的考察工具，你需要分析案例分析所对应能力有哪些,题本名称和代号的对应关系如下：
ID\t名称
beh\tBEI行为事件访谈
lgd\t无领导小组讨论
roleplay\t角色扮演
case\t案例分析
vision\t个人愿景
矩阵的输入格式为json，例如战略思维中"case": true，则表示个人case要考察战略思维， "beh": false则表示bei行为事件访谈不考察战略思维。
你需要基于此来判断vision要考察的能力有哪些
作用：帮助你来了解题本所考察的能力有哪些，考察的能力往往不止一个，要将"case": true所有能力都要算上
3. 案例分析题本的内容
输入内容为：{input}
格式为：一段文字
作用：帮助你了解题本的具体内容
# 评委指导手册撰写原则
1. 要告知评委题本给考生呈现的核心任务与挑战有哪些
2. 告知评委题本所考察的能力有哪些
3. 告知评委题本的核心任务与挑战是如何考察这些能力的
4. 告知评委考生面对这些挑战可能的好的行为表现和不好的行为表现有安歇
5. 考生可能采取哪些规避考察的策略，此处的回避策略是指考生故意回避自身短板的策略，这些策略本身具有欺骗性和掩饰性，可能引导评委出现高估其能力的表现

# 评委指导手册的内容和要求
1. 核心挑战和任务与考察点对应（要求每个考察点都要包含）
2. 考生可能的好的表现和不好的表现
3. 考生可能的回避策略及应对方法"""

INTEGRATE_SYSTEM_PROMPT = """你是一个文档整合专家，你擅于将材料严格按照格式做好排板。

# 输入
{all_handbooks}

# 输出要求
1. 不改变原文的任何内容
2. 将输入的各份材料整合成一份材料
3. 标题、格式要规范"""


class HandbookWorkflow:
    def __init__(self, llm):
        self.llm = llm

    async def _identify_tool_type(self, questionnaire_content: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="你是一个意图识别专家。请根据题本内容识别这是哪种测评工具。\n\n题本名称和代号的对应关系：\nID\t名称\nbeh\tBEI行为事件访谈\nlgd\t无领导小组讨论\nroleplay\t角色扮演\ncase\t案例分析\nvision\t个人愿景"),
            HumanMessage(content=f"请识别以下题本属于哪种测评工具：\n{questionnaire_content[:500]}")
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        result = response.content.lower()
        for tool_id, tool_name in TOOL_ID_MAP.items():
            if tool_name in result or tool_id in result:
                return tool_id
        return "unknown"

    async def _generate_beh_handbook(self, content: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=BEH_SYSTEM_PROMPT),
            HumanMessage(content=BEH_HUMAN_PROMPT.format(input=content))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def _generate_vision_handbook(self, content: str, competency_model: Dict, evaluation_matrix: Dict) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=VISION_SYSTEM_PROMPT.format(
                model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix),
                input=content
            )),
            HumanMessage(content="请生成个人愿景题本的评委指导手册")
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def _generate_roleplay_handbook(self, content: str, competency_model: Dict, evaluation_matrix: Dict) -> str:
        judge_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_JUDGE_SYSTEM_PROMPT.format(
                model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix),
                input=content
            )),
            HumanMessage(content="请生成角色扮演题本的评委指导手册")
        ])
        judge_chain = judge_prompt | self.llm
        judge_handbook = (await judge_chain.ainvoke({})).content

        actor_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_ACTOR_SYSTEM_PROMPT.format(
                judge_handbook=judge_handbook,
                input=content
            )),
            HumanMessage(content="请生成角色扮演题本的演员手册")
        ])
        actor_chain = actor_prompt | self.llm
        actor_handbook = (await actor_chain.ainvoke({})).content

        merge_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_MERGE_SYSTEM_PROMPT.format(
                actor_handbook=actor_handbook,
                judge_handbook=judge_handbook
            )),
            HumanMessage(content="请将评委手册和演员手册拼接在一起")
        ])
        merge_chain = merge_prompt | self.llm
        return (await merge_chain.ainvoke({})).content

    async def _generate_lgd_handbook(self, content: str, competency_model: Dict, evaluation_matrix: Dict) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=LGD_SYSTEM_PROMPT.format(
                model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix),
                input=content
            )),
            HumanMessage(content="请生成无领导小组讨论题本的评委指导手册")
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def _generate_case_handbook(self, content: str, competency_model: Dict, evaluation_matrix: Dict) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=CASE_SYSTEM_PROMPT.format(
                model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix),
                input=content
            )),
            HumanMessage(content="请生成案例分析题本的评委指导手册")
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def _integrate_handbooks(self, handbooks: List[str]) -> str:
        all_handbooks = "\n\n".join(handbooks)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=INTEGRATE_SYSTEM_PROMPT.format(all_handbooks=all_handbooks)),
            HumanMessage(content="请将所有评委手册整合成一份完整的文档")
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        questionnaires: List[Dict[str, str]]
    ) -> str:
        handbooks = []
        
        for q in questionnaires:
            tool_id = q.get("tool_id", "unknown")
            content = q.get("content", "")
            
            if tool_id == "beh":
                handbook = await self._generate_beh_handbook(content)
            elif tool_id == "vision":
                handbook = await self._generate_vision_handbook(content, competency_model, evaluation_matrix)
            elif tool_id == "roleplay":
                handbook = await self._generate_roleplay_handbook(content, competency_model, evaluation_matrix)
            elif tool_id == "lgd":
                handbook = await self._generate_lgd_handbook(content, competency_model, evaluation_matrix)
            elif tool_id == "case":
                handbook = await self._generate_case_handbook(content, competency_model, evaluation_matrix)
            else:
                handbook = content
            
            handbooks.append(handbook)
        
        if len(handbooks) > 1:
            return await self._integrate_handbooks(handbooks)
        elif handbooks:
            return handbooks[0]
        return ""