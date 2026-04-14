from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from src.schemas.questionnaire_schema import QuestionnaireSchema, QuestionnaireMeta, QuestionnaireContent

LGD_CHALLENGE_DESIGN_PROMPT = """你是一个人才评估专家，你能够基于需要考察的能力和考察的工具的挑战点来设计适合该工具的关键矛盾。

## 考察工具的挑战点
1. 观点冲突协调：组员意见对立时，需理性说服、求同存异，考察沟通协调与情绪把控能力。
2. 时间压力推进：讨论超时风险下，合理分配环节、推动节奏，考察时间管理与统筹意识。
3. 沉默组员激活：面对不发言成员，主动引导参与，考察团队意识与人际感知力。
4. 发散话题收拢：讨论偏离主题时，及时拉回核心，考察逻辑聚焦与方向把控能力。
5. 强势观点妥协：遇固执己见者，不争执不妥协，坚守逻辑底线，考察抗压与原则性。
6. 信息整合输出：零散观点汇总成完整结论，考察归纳总结与逻辑表达能力。
7. 角色定位平衡：兼顾个人表现与团队目标，不抢戏不划水，考察自我认知与大局观。
8. 突发分歧处理：突发激烈争执时，冷静化解矛盾，考察应急处理与情绪稳定性
9. 快速结构化思维：短时间内把零散信息搭成框架，避免逻辑混乱，考察系统性思考与框架搭建能力。
10. 多观点并行处理：同时接收多人观点，快速筛选、对比、取舍，考察信息处理与批判性思维。
11. 从发散到收敛：能先开放 brainstorm，再主动收拢方向、形成结论，考察思维的灵活性与聚焦能力。
12. 透过现象抓本质：不被表面问题带偏，识别核心矛盾与真实需求，考察深度分析与本质思维。
13. 逻辑自洽与闭环：观点前后一致、论证完整，不前后矛盾、漏洞百出，考察逻辑严谨性。
14. 换位思考与全局推演：站在整体目标而非个人立场预判结果，考察系统思维与全局观。
15. 打破惯性思维：对默认前提提出质疑，给出新思路，考察创新思维与独立判断能力。
16. 风险与利弊权衡：不只看优点，能主动想到隐患、代价与可行性，考察审慎思维与决策理性。

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
1. 问题表层化陷阱：讨论易停留在表面症状，需主动挖掘根本原因，考察深度剖析、拒绝主观臆断的问题分析能力。
2. 单一方案依赖：组员易局限一种思路，需主动提出多方案并评估风险可行性，考察科学决策与策略设计能力。
3. 只议不落地偏差：讨论偏重观点争论，需明确分工、节点与落地条件并监控闭环，考察结果导向与问题根治能力。"""

LGD_ENTERPRISE_CHALLENGE_PROMPT = """你是一个企业问题诊断专家，请你结合公司的背景材料，提取若干条企业当前面临的挑战点。请你结合输入材料中的企业背景，不要更换企业名称。

背景材料：
{background_material}

要求：提取3-5条企业当前面临的核心挑战点"""

LGD_FILE_EXTRACT_PROMPT = """请你通过链接访问文件，并且提取文件中的内容，按照良好的格式输出，不要遗漏关键信息，不要做二次解读，还原原文本。

输入的链接为：{file_url}"""

LGD_GENERATE_BACKGROUND_PROMPT = """请你查阅{company_name}相关的信息，并且生成该公司的历史、战略、目标、现状、挑战等方面的信息，不超过800字。

注意：一定要是该企业而不是其他企业"""

LGD_LEVEL_DUTIES_PROMPT = """你是一个岗位职责撰写专家，你现在要基于公司的某一个管理层级，来写一个该层级通用的管理职责。

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

LGD_CHALLENGE_DESIGN_PROMPT = """你是一个人才评估专家，你能够基于需要考察的能力和考察的工具的挑战点来设计适合该工具的关键矛盾。

# 输入内容
## 考察工具的挑战点
1. 观点冲突协调：组员意见对立时，需理性说服、求同存异，考察沟通协调与情绪把控能力。
2. 时间压力推进：讨论超时风险下，合理分配环节、推动节奏，考察时间管理与统筹意识。
3. 沉默组员激活：面对不发言成员，主动引导参与，考察团队意识与人际感知力。
4. 发散话题收拢：讨论偏离主题时，及时拉回核心，考察逻辑聚焦与方向把控能力。
5. 强势观点妥协：遇固执己见者，不争执不妥协，坚守逻辑底线，考察抗压与原则性。
6. 信息整合输出：零散观点汇总成完整结论，考察归纳总结与逻辑表达能力。
7. 角色定位平衡：兼顾个人表现与团队目标，不抢戏不划水，考察自我认知与大局观。
8. 突发分歧处理：突发激烈争执时，冷静化解矛盾，考察应急处理与情绪稳定性
9. 快速结构化思维：短时间内把零散信息搭成框架，避免逻辑混乱，考察系统性思考与框架搭建能力。
10. 多观点并行处理：同时接收多人观点，快速筛选、对比、取舍，考察信息处理与批判性思维。
11. 从发散到收敛：能先开放 brainstorm，再主动收拢方向、形成结论，考察思维的灵活性与聚焦能力。
12. 透过现象抓本质：不被表面问题带偏，识别核心矛盾与真实需求，考察深度分析与本质思维。
13. 逻辑自洽与闭环：观点前后一致、论证完整，不前后矛盾、漏洞百出，考察逻辑严谨性。
14. 换位思考与全局推演：站在整体目标而非个人立场预判结果，考察系统思维与全局观。
15. 打破惯性思维：对默认前提提出质疑，给出新思路，考察创新思维与独立判断能力。
16. 风险与利弊权衡：不只看优点，能主动想到隐患、代价与可行性，考察审慎思维与决策理性。

## 考察能力
{abilities}

# 输出要求
1. 针对每一个考察的能力设计出1-2个挑战点，每个挑战点不超过80字
2. 要结合所考察能力的内涵
# 输出要求
能力和挑战点都需要有，包括能力名称、能力含义、关键行为、挑战点；
# 输出示例
示例如下：
能力名称：解决问题
能力含义：指在面对工作任务中的障碍与挑战时，能够主动识别关键矛盾，运用逻辑分析与创新思维，制定有效策略并协调资源推动实施，最终消除障碍、达成目标的心理特质与行为表现。
关键行为：
1. 深度剖析：面对复杂工作或突发异常时，能迅速捕捉关键信息，通过数据比对、现场调研等方式深入挖掘问题背后的根本原因，避免主观臆断或仅处理表面现象。
2. 科学决策：基于根因分析设计至少 2 种针对性解决方案，评估可行性与风险，协调各方资源确保方案具备落地条件，明确责任分工与时间节点。
3. 结果导向：在执行过程中监控关键节点，及时纠偏应对突发状况，确保问题解决彻底，并形成标准化流程或案例沉淀防止复发。
挑战点：
1. 问题表层化陷阱：讨论易停留在表面症状，需主动挖掘根本原因，考察深度剖析、拒绝主观臆断的问题分析能力。
2. 单一方案依赖：组员易局限一种思路，需主动提出多方案并评估风险可行性，考察科学决策与策略设计能力。
3. 只议不落地偏差：讨论偏重观点争论，需明确分工、节点与落地条件并监控闭环，考察结果导向与问题根治能力."""

LGD_CHALLENGE_MATCH_PROMPT = """你是一个人才评估专家，你擅长于设计贴合实际工作场景的任务来考察候选人。请你结合企业当前面临的挑战、无领导小组讨论可以设计的挑战点、考生的管理层级和职责来输出。

# 输入
考察点和挑战点：{challenge_points}
企业面临的挑战：{enterprise_challenges}
考生的管理层级和职责：{level_duties}

# 输出要求
1. 结合公司当前面临的挑战
2. 要结合考察点和考察工具适合设计的挑战点
3. 针对每一个考察工具的挑战点都有一个对应的企业挑战点
4. 必须是当前材料中的企业相关的挑战
# 输出要求
能力和挑战点都需要有
考察点：输入的考察点{challenge_points}
企业挑战点：企业层面面临的挑战点{enterprise_challenges}
任务说明：任务必须要克服企业面临的挑战点，且能够与{challenge_points}的考察点和挑战点可以契合。
任务必须要贴合考生的管理层级和职责：{level_duties}，不要超越该职责和层级，也让不要低于它
# 输出示例
考察点：解决问题
企业挑战点：公司面临效率提升瓶颈，基层交付延迟问题突出，影响整体战略落地，这是企业当前核心挑战之一。
任务说明：结合企业该挑战，分析问题根源并规划解决路径."""

LGD_BOOK_GENERATION_PROMPT = """你是一个命题专家，现在题本的框架设计已经完成，但是需要你结合企业一些背景信息完成题本的完整设计。只需要生成一个完成的题本，但是要考察所有需要考察的能力。同时满足用户的要求。请不要在题本设计中更改企业名称，如实根据输入文件中的企业名称、现状和挑战点来撰写。

# 用户要求
{requirement}

# 企业挑战点
{challenge_matches}

# 背景材料
{background_material}

# 题本内容要求

一、 背景信息
撰写要求如下：
1. 融合输入材料中的所有企业挑战点：{challenge_matches}
2. 先扬后抑，正面描写且有挑战
3. 用词严谨准确，不要引起误会和歧义
4. 用词规范，不要口语化
5. 尽量引用文件中领导的讲话原文，不要在其中有任何出题人的判断和态度，保持客观中立
6. 不要机械拼接，要求过渡自然，语句平顺，一气呵成
7. 总字数不超过800字
8. 在背景信息中不涉及任何和考生职责和任务相关的信息仅仅只描述企业背景
9. 背景信息中要引出待讨论的问题，但是不用讲得太细，只需要不让任务和背景信息看起来太割裂

二、 任务说明
任务撰写要求如下：
1. 一句话描述本次讨论的目标和最终产出；
2. 按照定位问题、分析原因、提出方案三步骤将任务分解为三个子任务，但是任务中不要体现这些字眼，也不要体现"分解"等字眼。拆分要有逻辑，只有先完成任务1才能完成任务2
3. 任务只能选择一个话题，只解决一个问题，不要涉及话题太多、太广。
4. 任务不能对偏向于某一个专业、岗位背景的考生，该任务必须是全公司所有领域、岗位的员工对该问题所掌握的信息是基本对等的，不存在专业、岗位所带来的信息差。

三、 会议议程与注意事项
固定内容如下：
1、先独自进行材料的阅读与讨论前的准备，时间为30分钟；
2、准备结束后，轮流陈述个人观点，每位成员发言时间不超过2分钟，发言不指定顺序；
3、个人观点陈述完毕后，进入自由讨论环节，讨论时间为30分钟；在自由讨论环节中，鼓励个人踊跃表述自己的见解，就主题形成一致意见，即得出一个小组成员共同认可的结论；讨论过程中请用编号称呼对方，禁止采用投票表决的形式进行观点的抉择；
4、讨论期间，严格遵循会议秩序，请坐在座位上，不允许同时有两个及以上的成员起立、走动而造成会议混乱；
5、小组讨论的产出成果质量将会影响小组的整体评分；小组成员对产出成果的贡献度将会影响其个人评分；
6、在个人发言和小组讨论期间，请不要观察评委席，也不用就任何问题请示评委席，自主行动，全身心投入讨论中；
7、请将讨论的产出成果输出在白板上，自由讨论结束后，委派一名代表汇报小组的成果，时间为3分钟。

# 输出示例
一、 背景描述
岚图汽车党委书记、董事长卢放在公司2026年工作会上的讲话中提到，十四五期间，岚图汽车在"体制机制创新"上，探索了适应新时代竞争的现代企业治理模式。构建了以OKR为导向的目标管理体系，组织实现敏捷化，管理实现扁平化，初步建成了研产供销服全价值链协同的体系。2026年，要持续推进OKR管理，团结一致向前进，打赢体制机制创新之仗，持续为高质量发展注入新动能。
实践证明，OKR在一个企业内部的推行落地也并不总是一帆风顺的，往往会由于公司战略、组织文化、制度流程、评价导向、人员能力等方面的特殊性，导致企业在推行OKR的过程中，或多或少都遇到"水土不服"的问题。

二、 讨论任务
假设各位是岚图OKR改革委员会的成员，今天是委员会的例会，请结合你过去的观察和实践，思考：
1. 在岚图OKR管理实践中，当前还存在的最大的问题是什么？
2. 导致该问题出现的最深层的原因是什么？
3. 2026年，我们应该采取哪些措施才能解决该问题？

三、 会议议程与注意事项
1、先独自进行材料的阅读与讨论前的准备，时间为30分钟；
2、准备结束后，轮流陈述个人观点，每位成员发言时间不超过2分钟，发言不指定顺序；
3、个人观点陈述完毕后，进入自由讨论环节，讨论时间为30分钟；在自由讨论环节中，鼓励个人踊跃表述自己的见解，就主题形成一致意见，即得出一个小组成员共同认可的结论；讨论过程中请用编号称呼对方，禁止采用投票表决的形式进行观点的抉择；
4、讨论期间，严格遵循会议秩序，请坐在座位上，不允许同时有两个及以上的成员起立、走动而造成会议混乱；
5、小组讨论的产出成果质量将会影响小组的整体评分；小组成员对产出成果的贡献度将会影响其个人评分；
6、在个人发言和小组讨论期间，请不要观察评委席，也不用就任何问题请示评委席，自主行动，全身心投入讨论中；
7、请将讨论的产出成果输出在白板上，自由讨论结束后，委派一名代表汇报小组的成果，时间为3分钟。

# 输出要求
1. 背景信息必须是与{background_material}中的企业背景，不能是其他企业,并且充分利用背景材料中的信息
2. 背景材料中只需要如实的描述事实，包括领导讲话原文、数据等，在引用时，一定要在背景材料中说明，从哪个文件中引用了谁的讲话，讲话内容必须是原文；
3. 背景材料不要编造材料，尊重事实，也不要描述一些态度、观点、看法，产生一些错误引导
4. 背景材料在描述挑战和问题时，也不要悲观消极，要积极、正面地描述

# 输出示例
一、 背景描述
岚图汽车党委书记、董事长卢放在公司2026年工作会上的讲话中提到，十四五期间，岚图汽车在"体制机制创新"上，探索了适应新时代竞争的现代企业治理模式。构建了以OKR为导向的目标管理体系，组织实现敏捷化，管理实现扁平化，初步建成了研产供销服全价值链协同的体系。2026年，要持续推进OKR管理，团结一致向前进，打赢体制机制创新之仗，持续为高质量发展注入新动能。
实践证明，OKR在一个企业内部的推行落地也并不总是一帆风顺的，往往会由于公司战略、组织文化、制度流程、评价导向、人员能力等方面的特殊性，导致企业在推行OKR的过程中，或多或少都遇到"水土不服"的问题。

二、 讨论任务
假设各位是岚图OKR改革委员会的成员，今天是委员会的例会，请结合你过去的观察和实践，思考：
1. 在岚图OKR管理实践中，当前还存在的最大的问题是什么？
2. 导致该问题出现的最深层的原因是什么？
3. 2026年，我们应该采取哪些措施才能解决该问题？

三、 会议议程与注意事项
1、先独自进行材料的阅读与讨论前的准备，时间为30分钟；
2、准备结束后，轮流陈述个人观点，每位成员发言时间不超过2分钟，发言不指定顺序；
3、个人观点陈述完毕后，进入自由讨论环节，讨论时间为30分钟；在自由讨论环节中，鼓励个人踊跃表述自己的见解，就主题形成一致意见，即得出一个小组成员共同认可的结论；讨论过程中请用编号称呼对方，禁止采用投票表决的形式进行观点的抉择；
4、讨论期间，严格遵循会议秩序，请坐在座位上，不允许同时有两个及以上的成员起立、走动而造成会议混乱；
5、小组讨论的产出成果质量将会影响小组的整体评分；小组成员对产出成果的贡献度将会影响其个人评分；
6、在个人发言和小组讨论期间，请不要观察评委席，也不用就任何问题请示评委席，自主行动，全身心投入讨论中；
7、请将讨论的产出成果输出在白板上，自由讨论结束后，委派一名代表汇报小组的成果，时间为3分钟。"""


class LGDWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        background_file_content: Optional[str] = None,
        requirement: str = ""
    ) -> str:
        print(f"[LGDWorkflow] 开始生成题本")
        print(f"[LGDWorkflow] background_file_content: {background_file_content[:200] if background_file_content else 'None'}...")
        
        dimensions = competency_model.get("dimensions", [])
        level = competency_model.get("level", "基层经理")
        
        abilities = "\n".join([
            f"- {d.get('name', '')}: {d.get('description', '')}"
            for d in dimensions
        ])
        
        background_material = background_file_content or ""
        
        # Step 1: 考生层级与职责 (133431)
        level_duties_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=LGD_LEVEL_DUTIES_PROMPT.format(level=level)),
            HumanMessage(content="请生成管理层级职责")
        ])
        level_duties = (await (level_duties_prompt | self.llm).ainvoke({})).content
        
        # Step 2: 考察工具挑战点设计 (198460)
        challenge_design_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=LGD_CHALLENGE_DESIGN_PROMPT.format(abilities=abilities)),
            HumanMessage(content="请设计挑战点")
        ])
        challenge_points = (await (challenge_design_prompt | self.llm).ainvoke({})).content
        
        # Step 3: 条件分支 - 检查是否有背景材料
        # 如果没有背景材料，生成默认背景材料
        print(f"[LGDWorkflow] 背景材料长度: {len(background_material) if background_material else 0}")
        
        if not background_material or background_material.strip() == "":
            print(f"[LGDWorkflow] 走无背景材料分支，生成默认背景")
            # 生成默认背景材料（模拟Coze中155555节点）
            generate_bg_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=LGD_GENERATE_BACKGROUND_PROMPT.format(company_name="一家知名企业")),
                HumanMessage(content="请生成企业背景")
            ])
            generated_background = (await (generate_bg_prompt | self.llm).ainvoke({})).content
            print(f"[LGDWorkflow] 生成的默认背景: {generated_background[:200]}...")
            enterprise_challenges_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=LGD_ENTERPRISE_CHALLENGE_PROMPT.format(background_material=generated_background)),
                HumanMessage(content="请提取企业挑战点")
            ])
            enterprise_challenges = (await (enterprise_challenges_prompt | self.llm).ainvoke({})).content
            background_material = generated_background
        else:
            print(f"[LGDWorkflow] 走有背景材料分支，使用用户提供的背景材料")
            # 使用用户提供的背景材料，提取企业挑战点
            enterprise_challenges_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=LGD_ENTERPRISE_CHALLENGE_PROMPT.format(background_material=background_material)),
                HumanMessage(content="请提取企业挑战点")
            ])
            enterprise_challenges = (await (enterprise_challenges_prompt | self.llm).ainvoke({})).content
            print(f"[LGDWorkflow] 企业挑战点: {enterprise_challenges[:200]}...")
        
        # Step 4: 考点-挑战点-任务配对 (197594)
        match_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=LGD_CHALLENGE_MATCH_PROMPT.format(
                challenge_points=challenge_points,
                enterprise_challenges=enterprise_challenges,
                level_duties=level_duties
            )),
            HumanMessage(content="请匹配挑战点")
        ])
        challenge_matches = (await (match_prompt | self.llm).ainvoke({})).content
        
        # Step 5: 题本生成 (125634)
        final_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=LGD_BOOK_GENERATION_PROMPT.format(
                requirement=requirement,
                challenge_matches=challenge_matches,
                background_material=background_material
            )),
            HumanMessage(content="请生成完整的LGD题本")
        ])
        
        response = await (final_prompt | self.llm).ainvoke({})
        
        # 构建统一JSON格式
        meta = QuestionnaireMeta(
            tool_id="lgd",
            tool_name="无领导小组讨论",
            level=competency_model.get("level"),
            duration=90,
            generated_at=datetime.now().isoformat()
        )
        
        content = QuestionnaireContent(
            scenario=response.content[:500] if response.content else "LGD讨论场景"
        )
        
        schema = QuestionnaireSchema(meta=meta, content=content)
        return schema.to_json_string()