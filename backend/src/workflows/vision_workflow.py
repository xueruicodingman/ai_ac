from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from src.schemas.questionnaire_schema import QuestionnaireSchema, QuestionnaireMeta, QuestionnaireContent

VISION_CHALLENGE_DESIGN_PROMPT = """你是一个人才评估专家，你能够基于需要考察的能力和考察的工具的挑战点来设计适合该工具的关键矛盾。

## 考察工具的挑战点
1. 对齐企业战略的挑战
要求候选人必须明确引用公司年度重点 / 战略方向（如：数字化、成本优化、客户满意度、新业务拓展等）。
不能只谈 "我要成长"，必须说明本职工作如何支撑公司某一条战略落地。
测评点：战略理解、组织对齐意识、岗位价值定位。

2. 落地到本职工作的颗粒度挑战
要求愿景不能空泛，必须拆解到：本职核心职责、可量化的工作成果、具体改进 / 提升方向
禁止只谈 "做好本职"，必须有可观察、可评价的行动与目标。
测评点：目标清晰度、执行力意识、务实性。

3. 个人能力与企业需求匹配的挑战
如何弥补岗位短板
如何把个人成长转化为岗位绩效 / 团队价值
测评点：自我认知、成长动机、学习意识。

4. 资源与边界认知挑战
实现愿景需要公司 / 部门提供什么支持
如何在现有岗位职责边界内创造更大价值
如何协同上下游 / 跨部门支撑整体目标
测评点：资源意识、协作思维、边界感与大局观。

5. 短期贡献与长期发展平衡挑战
未来 1 年：为本职 / 部门带来什么直接成果
未来 2–3 年：如何成长为更支撑企业战略的角色
测评点：长期视角、结果导向。

## 考察能力
{abilities}

## 输出要求
1. 针对每一个考察的能力设计出1-2个挑战点，每个挑战点不超过80字
2. 要结合所考察能力的内涵

能力和挑战点都需要有，包括能力名称、能力含义、关键行为、挑战点；

## 输出示例
能力名称：解决问题
能力含义：指在面对工作任务中的障碍与挑战时，能够主动识别关键矛盾，运用逻辑分析与创新思维，制定有效策略并协调资源推动实施，最终消除障碍、达成目标的心理特质与行为表现。
关键行为：
1. 深度剖析：面对复杂工作或突发异常时，能迅速捕捉关键信息，通过数据比对、现场调研等方式深入挖掘问题背后的根本原因，避免主观臆断或仅处理表面现象。
2. 科学决策：基于根因分析设计至少 2 种针对性解决方案，评估可行性与风险，协调各方资源确保方案具备落地条件，明确责任分工与时间节点。
3. 结果导向：在执行过程中监控关键节点，及时纠偏应对突发状况，确保问题解决彻底，并形成标准化流程或案例沉淀防止复发。
挑战点：
1. 要求愿景不能是口号，必须拆成阶段目标、时间节点、责任边界
2. 要求在愿景中长期部分说明问题解决后，如何形成经验、流程或案例，避免同类问题重复发生。
3. 要求不能只写目标和成长，必须结合企业规划，识别本职工作中 1–2 个真实存在的障碍 / 痛点，并说明其对公司目标的影响"""

VISION_ENTERPRISE_CHALLENGE_PROMPT = """你是一个企业问题诊断专家，请你结合公司的背景材料，提取若干条企业当前面临的挑战点.

背景材料：
{background_material}

要求：提取3-5条企业当前面临的核心挑战点"""

VISION_LEVEL_DUTIES_PROMPT = """你是一个岗位职责撰写专家，你现在要基于公司的某一个管理层级，来写一个该层级通用的管理职责。

# 输入
管理层级：{level}

# 输出要求
输出管理层级、管理层级对应的管理职责，每一条职责不超过30字

# 输出示例
管理层级：基层经理
管理职责：
1. 落实公司战略与部门目标，分解任务至下属，确保高效落地。
2. 带领团队完成业绩指标，监督工作进度，及时纠偏补位。
3. 负责下属日常管理、考勤考核，规范工作流程与行为。
4. 开展下属岗前培训、技能指导，助力团队能力提升。
5. 协调跨岗位 / 跨部门协作，解决团队工作中的常规问题。
6. 关注下属工作状态，做好沟通激励，提升团队凝聚力。
7. 上报团队工作情况、问题与建议，配合上级统筹管理。
8. 把控工作质量与安全，防范基层工作中的各类风险。"""

VISION_CHALLENGE_MATCH_PROMPT = """你是一个人才评估专家，你擅长于设计贴合实际工作场景的任务来考察候选人。请你结合企业当前面临的挑战、个人愿景可以设计的挑战点、考生的管理层级和职责来输出。

# 输入
考察点和挑战点：{challenge_points}
企业面临的挑战：{enterprise_challenges}
考生的管理层级和职责：{level_duties}

# 输出要求
1. 结合公司当前面临的挑战
2. 要结合考察点和考察工具适合设计的挑战点
3. 针对每一个考察工具的挑战点都有一个对应的企业挑战点
4. 能力和挑战点都需要有，包括考察点、企业挑战点、任务说明

# 输出示例
考察点：解决问题
企业挑战点：公司面临效率提升瓶颈，基层交付延迟问题突出，影响整体战略落地，这是企业当前核心挑战之一。
任务说明：结合企业该挑战，分析问题根源并规划解决路径。"""

VISION_BOOK_GENERATION_PROMPT = """你是一个命题专家，现在题本的框架设计已经完成，但是需要你结合企业一些背景信息完成题本的完整设计。只需要生成一套题本，考察所有需要考察的能力。同时满足用户的要求。

# 用户要求
{requirement}

# 企业挑战点
{challenge_matches}

# 背景材料
{background_material}

# 题本内容

一、 任务说明
固定内容如下：
本环节为个人愿景，您有60分钟的时间进行准备，学员请在规定时间内，根据第三部分的任务要求，梳理思路，并将您的思路呈现在A0白纸上（注意：书写字体太小会影响评委阅读）。
准备时间结束后，进行个人汇报，并回答评委的提问，其中汇报时长不超过15分钟。个人愿景模拟总时长为30分钟。

二、 背景信息
撰写要求如下：
1. 融合输入材料中的所有企业挑战点
2. 先扬后抑，正面描写且有挑战
3. 用词严谨准确，不要引起误会和歧义
4. 用词规范，不要口语化
5. 尽量引用文件中领导的讲话原文，不要在其中有任何出题人的判断和态度，保持客观中立
6. 不要机械拼接，要求过渡自然，语句平顺，一气呵成
7. 总字数不超过800字
8. 在背景信息中不涉及任何和考生职责和任务相关的信息仅仅只描述企业背景
9. 背景信息不要与任务说明中的任务太割裂，要在背景信息中稍微引出任务

三、 任务说明
撰写要求如下：
1. 从诸多企业挑战点选择一个挑战点作为任务的核心
2. 该挑战点必须具备普遍性，是与公司的所有领域、专业、岗位都紧密相关
3. 任务字数不超过100字，任务要清晰、明确，让考生知道如何算是完成任务
4. 任务不能对偏向于某一个专业、岗位背景的考生，该任务必须是全公司所有领域、岗位的员工对该问题所掌握的信息是基本对等的，不存在专业、岗位所带来的信息差
5. 任务的来源和背景必须在背景信息中被提及过

# 输出示例
一、 任务说明
本环节为个人愿景，您有60分钟的时间进行准备，学员请在规定时间内，根据第三部分的任务要求，梳理思路，并将您的思路呈现在A0白纸上（注意：书写字体太小会影响评委阅读）。
准备时间结束后，进行个人汇报，并回答评委的提问，其中汇报时长不超过15分钟。个人愿景模拟总时长为30分钟。
 
二、 背景信息
复盘是对项目、任务或事件，通过还原过程、对比目标与结果、分析差异根因、提炼可复用经验、制定改进措施，将单次经历转化为结构化能力与长期竞争力的闭环学习方法。其核心目标是：从过去的行动中学习，沉淀组织经验、减少重复失误、优化决策流程，推动持续迭代改进，把个人经验转化为组织能力，以最低成本实现长效增长。
 
三、 任务要求
请您立足于您的本职工作，对您过去一年的工作做一次系统复盘。"""

VISION_GENERATE_BACKGROUND_PROMPT = """请你查阅{company_name}相关的信息，并且生成该公司的历史、战略、目标、现状、挑战等方面的信息，不超过800字。"""


class VisionWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        background_file_content: Optional[str] = None,
        requirement: str = ""
    ) -> str:
        dimensions = competency_model.get("dimensions", [])
        level = competency_model.get("level", "基层经理")
        
        abilities = "\n".join([
            f"- {d.get('name', '')}: {d.get('description', '')}"
            for d in dimensions
        ])
        
        background_material = background_file_content or ""
        
        # Step 1: 考生层级与职责 (133431)
        level_duties_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=VISION_LEVEL_DUTIES_PROMPT.format(level=level)),
            HumanMessage(content="请生成管理层级职责")
        ])
        level_duties = (await (level_duties_prompt | self.llm).ainvoke({})).content
        
        # Step 2: 考察工具挑战点设计 (198460)
        challenge_design_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=VISION_CHALLENGE_DESIGN_PROMPT.format(abilities=abilities)),
            HumanMessage(content="请设计挑战点")
        ])
        challenge_points = (await (challenge_design_prompt | self.llm).ainvoke({})).content
        
        # Step 3: 条件分支 - 检查是否有背景材料
        if not background_material or background_material.strip() == "":
            # 生成默认背景材料（模拟Coze中155555节点）
            generate_bg_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=VISION_GENERATE_BACKGROUND_PROMPT.format(company_name="一家知名企业")),
                HumanMessage(content="请生成企业背景")
            ])
            generated_background = (await (generate_bg_prompt | self.llm).ainvoke({})).content
            enterprise_challenges_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=VISION_ENTERPRISE_CHALLENGE_PROMPT.format(background_material=generated_background)),
                HumanMessage(content="请提取企业挑战点")
            ])
            enterprise_challenges = (await (enterprise_challenges_prompt | self.llm).ainvoke({})).content
            background_material = generated_background
        else:
            # 使用用户提供的背景材料，提取企业挑战点
            enterprise_challenges_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=VISION_ENTERPRISE_CHALLENGE_PROMPT.format(background_material=background_material)),
                HumanMessage(content="请提取企业挑战点")
            ])
            enterprise_challenges = (await (enterprise_challenges_prompt | self.llm).ainvoke({})).content
        
        # Step 4: 考点-挑战点-任务配对 (197594)
        match_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=VISION_CHALLENGE_MATCH_PROMPT.format(
                challenge_points=challenge_points,
                enterprise_challenges=enterprise_challenges,
                level_duties=level_duties
            )),
            HumanMessage(content="请匹配挑战点")
        ])
        challenge_matches = (await (match_prompt | self.llm).ainvoke({})).content
        
        # Step 5: 题本生成 (125634)
        final_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=VISION_BOOK_GENERATION_PROMPT.format(
                requirement=requirement,
                challenge_matches=challenge_matches,
                background_material=background_material
            )),
            HumanMessage(content="请生成完整的个人愿景题本")
        ])
        
        response = await (final_prompt | self.llm).ainvoke({})
        
        # 构建统一JSON格式
        meta = QuestionnaireMeta(
            tool_id="vision",
            tool_name="个人愿景",
            level=competency_model.get("level"),
            duration=30,
            generated_at=datetime.now().isoformat()
        )
        
        content = QuestionnaireContent(
            scenario=response.content[:500] if response.content else "个人愿景场景"
        )
        
        schema = QuestionnaireSchema(meta=meta, content=content)
        return schema.to_json_string()