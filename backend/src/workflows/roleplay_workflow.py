from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from src.schemas.questionnaire_schema import QuestionnaireSchema, QuestionnaireMeta, QuestionnaireContent, RoleInfo

ROLEPLAY_CHALLENGE_DESIGN_PROMPT = """你是一个人才评估专家，你能够基于需要考察的能力和考察的工具的挑战点来设计适合该工具的关键矛盾。

## 考察工具的挑战点
1. 指令模糊：布置工作时重点不清、标准不明，下级难以执行，体现不出管理清晰度。
2. 沟通生硬：语气强势、缺乏引导，只会压任务不做解释，容易引发对立情绪。
3. 缺乏倾听：只顾下达要求，不听取下级困难与建议，显得独断且不接地气。
4. 问题处理简单化：下级提出问题时只会批评或催促，不会分析原因、给出方法。
5. 分寸失衡：要么过于温和没权威，要么过于严厉不近人情，管理尺度把握不准。
6. 应变不足：面对下级反驳、推诿或突发状况，容易慌乱、语塞或情绪失控。
7. 目标拆解不足：只会提整体要求，不会把任务拆成可落地步骤，下级无从下手。
8. 激励与施压失衡：要么只批评不鼓励，要么只安抚不推动，无法有效调动下级积极性。
9. 边界感模糊：过度插手细节或放任不管，管得太死或太松，管理节奏混乱。
10. 矛盾回避：遇到下级推诿、意见不合时不敢直面冲突，绕开问题不解决。
11. 决策犹豫：面对下级请示或争议时反复不定，缺乏果断性与决断力。
12. 反馈无效：只说 "不行""重做"，不指出具体问题和改进方向，指导价值低。

## 考察能力
{abilities}

## 输出要求
1. 针对每一个考察的能力设计出1-2个挑战点，每个挑战点不超过80字
2. 要结合所考察能力的内涵

能力和挑战点都需要有，包括胜任力（能力名称、能力含义、关键行为）和对应的挑战点；

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

ROLEPLAY_LEVEL_DUTIES_PROMPT = """你是一个岗位职责撰写专家，你现在要基于公司的某一个管理层级，来写一个该层级通用的管理职责。

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

ROLEPLAY_GENERATE_CONFLICT_SCENARIOS_PROMPT = """请你查阅公开资料，包括各类企业现状和管理学书籍，了解企业内部在上下级之间沟通不同问题的冲突场景。请你尽可能多地罗列这样的冲突场景。输出要求如下：
1. 标题和内容都要客观中立，不要有任何评价和判断对错，只描述事实；
2. 要明确冲突双方的分别是谁以及其各自的职责是什么；
3. 要分别阐述冲突双方在冲突中各自的诉求和对问题的理解；

# 输出示例
场景1：工作计划节奏冲突
- 场景介绍：部门负责人根据企业整体进度要求、外部合作节点等，制定部门及下属的工作推进计划；业务骨干或基层员工结合自身工作量、工作环节的复杂程度，自行安排具体工作节奏，双方在计划推进的快慢、节点设置上存在分歧。
- 岗位：部门负责人 → 业务骨干/员工
- 上级视角：以整体进度、外部要求倒排计划，注重计划的时效性和整体性，要求下属严格按照既定节奏推进，确保整体目标按时达成。
- 下级视角：以实际工作量、环节复杂度安排节奏，更关注工作质量和自身执行效率，希望根据具体工作情况灵活调整推进速度。"""

ROLEPLAY_EXTRACT_CONFLICT_FROM_FILE_PROMPT = """请你通过链接访问文件，并且提取文件中的内容，提取背景材料中所反映出来企业内部在上下级之间沟通不同问题的冲突场景。请你尽可能多地罗列这样的冲突场景。输出要求如下：
1. 标题和内容都要客观中立，不要有任何评价和判断对错，只描述事实；
2. 要明确冲突双方的分别是谁以及其各自的职责是什么；
3. 要分别阐述冲突双方在冲突中各自的诉求和对问题的理解；

# 输出示例
场景1：工作计划节奏冲突
- 场景介绍：部门负责人根据企业整体进度要求、外部合作节点等，制定部门及下属的工作推进计划；业务骨干或基层员工结合自身工作量、工作环节的复杂程度，自行安排具体工作节奏，双方在计划推进的快慢、节点设置上存在分歧。
- 岗位：部门负责人 → 业务骨干/员工
- 上级视角：以整体进度、外部要求倒排计划，注重计划的时效性和整体性，要求下属严格按照既定节奏推进，确保整体目标按时达成。
- 下级视角：以实际工作量、环节复杂度安排节奏，更关注工作质量和自身执行效率，希望根据具体工作情况灵活调整推进速度。"""

ROLEPLAY_CORE_SCENE_SELECTION_PROMPT = """你是一个人才评估专家，你擅长于设计贴合实际工作场景的任务来考察候选人。请你结合考生所处的层级、考察点和挑战点设计，从企业沟通冲突场景中选择3-5个适配的场景。

# 输入
考察点和挑战点设计：{challenge_points}
企业沟通冲突场景：{conflict_scenarios}
考生的层级和职责：{level_duties}

# 输出要求
1. 结合题本的考察点和挑战点设计
2. 考生的层级和职责，场景必须是考生在日常工作中最经常遇到的
3. 要结合考察点和考察工具适合设计的挑战点
4. 针对每一个考察点都要选择1-2个冲突场景

# 输出内容
1. 考察点
要求包括考察项和所考察的考察项中的哪一条行为标准
2. 冲突场景
1-2个，要明确冲突双方的分别是谁以及其各自的职责是什么、要分别阐述冲突双方在冲突中各自的诉求和对问题的理解、要明确每个冲突场景所对应考察的能力的哪一条或者哪几条行为标准

# 输出示例
考察点：目标管理
考察行为：面对工作调整或临时任务时，主动沟通影响、同步共识，在保障核心目标达成的前提下有序推进。
冲突场景1：工作计划节奏冲突
- 场景介绍：部门负责人根据企业整体进度要求、外部合作节点等，制定部门及下属的工作推进计划；业务骨干或基层员工结合自身工作量、工作环节的复杂程度，自行安排具体工作节奏，双方在计划推进的快慢、节点设置上存在分歧。
- 岗位：部门负责人 → 业务骨干/员工
- 上级视角：以整体进度、外部要求倒排计划，注重计划的时效性和整体性，要求下属严格按照既定节奏推进，确保整体目标按时达成。
- 下级视角：以实际工作量、环节复杂度安排节奏，更关注工作质量和自身执行效率，希望根据具体工作情况灵活调整推进速度。"""

ROLEPLAY_ROLE_TASK_DESIGN_PROMPT = """你是一个管理案例撰写专家，你现在需要围绕若干个场景，来编写对应的一些背景信息，来完善这个案例。要求考生在这些冲突场景中必须是上级角色，即将沟通的下级角色只能有一个。

# 输入内容
你将会得到若干个如下的冲突场景(示例)：
考察点：目标管理
考察行为：面对工作调整或临时任务时，主动沟通影响、同步共识，在保障核心目标达成的前提下有序推进。
冲突场景1：工作计划节奏冲突
- 场景介绍：部门负责人根据企业整体进度要求、外部合作节点等，制定部门及下属的工作推进计划；业务骨干或基层员工结合自身工作量、工作环节的复杂程度，自行安排具体工作节奏，双方在计划推进的快慢、节点设置上存在分歧。
- 岗位：部门负责人 → 业务骨干/员工
- 上级视角：以整体进度、外部要求倒排计划，注重计划的时效性和整体性，要求下属严格按照既定节奏推进，确保整体目标按时达成。
- 下级视角：以实际工作量、环节复杂度安排节奏，更关注工作质量和自身执行效率，希望根据具体工作情况灵活调整推进速度。

# 输出内容与要求
1. 公司简介
内容：包括公司的历史渊源、主营业务、市场环境、现状与挑战
字数：800字以内
段落：最多分2段

2. 角色简介
内容：冲突双方中上下级的角色介绍，主要是让人口学信息，加入公司的时间，业内的影响力，从业经验，过往的业绩。上下级角色会参与参与到所有的场景中。
字数：200字以内
段落：1段
其他要求：要结合考生的在实际工作中的层次和职责{level}，同时考生在冲突场景中必须是上级角色，下级的角色只有一个，且会参与到各个冲突场景中。

3. 任务介绍
固定模板如下，标记星号的内容需要你来填充：
你现在有30分钟的时间通读下面的材料并准备李明月的谈话，你和他的谈话最多持续15分钟，时间用完后您会被强制打断并结束谈话。通过本次谈话，您需要针对材料中提到的问题与他共识解决办法。
假设今天的日期是****年**月**日。
注：在模拟过程中，对方（工作人员出演）将称呼您为**经理。"""

ROLEPLAY_CONFLICT_EXPAND_PROMPT = """你是一个案例撰写专家，你现在需要撰写一些沟通冲突场景的背景。

# 你的输入
公司、角色、任务背景：{background}
若干个冲突场景：{scenarios}

# 输出要求
1. 将各个冲突场景进行详细描述，尤其是要将冲突场景的背景信息描述清楚，体现两难之处，并且是任何行业都通用。同样要结合公司、角色、任务背景

2. 都必须要涉及到上下级角色，下级以直接身份身处于场景之中，上级只是第三者视角

# 输出格式
字数：不超过1000字
关键信息数量：不低于5项
输出格式：按照项目符号对每个冲突场景的背景信息输出"""

ROLEPLAY_CONFLICT编排_PROMPT = """你是一个案例撰写专家，公文筐命题专家，你现在需要撰写一些沟通冲突场景的背景。

# 你的输入
公司、考生角色、任务背景：{background}
若干个冲突场景：{scenarios}

# 输出要求
将各个冲突场景的背景信息分散糅合在一封封发给考生角色的邮件中，邮件有以下几种类型：
1. 来自上级的邮件
2. 来自业务上下游协同部门的邮件
3. 来自于人力资源的邮件
4. 来自财务部门的邮件
5. 来自于其他下属的邮件
你需要根据冲突场景的类型，选择一种合适邮件形式

数量要求：要求邮件数量不低于3项。
内容要求：每一封邮件必须符合发件人和收件人的任务角色，收件人就是考生角色；只需要包含若干个完整的邮件信息，不包含任何其他内容
字数要求：每一封邮件500-1000字之间

# 输出格式与示例
标题：概括邮件内容的标题
发信人 ： 蒋慕云@lvchi.com（邮箱要体现公司名称）
收信人 ： 您@lvchi.com（邮箱要体现公司名称）
主题：研发部门对人力资源工作的建议
陈经理：
很高兴公司在加大对人力资源工作的投入，期待您能带领人力资源顺利完成转型。有一些情况我亟需向您反馈，因为已经影响到了业务工作的开展。研发部门的HRBP李明月确实是一位工作负责、踏实、有经验的员工。
对招聘工作也是一丝不苟。但是从结果来看，却不尽如人意。在上个月有两次失败的案例，我想也足够让我们引起注意：
· 研发部门急需一名行业大牛来推进一个关键项目，但由于公司的人力资源政策要求所有高级别的任命都必须经过总部审批，导致候选人迟迟无法入职。最终该候选人被友商"截胡"。研发的同事们对此非常愤怒，认为人力资源的工作过于强调流程是为了保护人力资源自己，并不是在驱动业务发展。
· 软件工程中心目前正处于人力极其短缺的状况，尤其是核心技术骨干。在过去的招聘中，也并不是没有合适的候选人，而是人力资源在薪资水平上管理太严格，我们的薪酬竞争力远不如友商，导致我们在招聘市场上竞争力太弱，如果这个情况得不到改善，软件工程中心的高强度、高负荷的工作不仅影响工作质量、项目开展，还会影响团队稳定性，给管理者带来极大的管理难度。
以上两个方面的问题，希望能够引起您的重视，另外，现在的HRBP习惯于以往的人力资源工作模式，习惯于从政策、合规的角度开展工作，上述两个失败的案例与此紧密相关，我们需要能够提供定制化解决方案的HRBP，希望您能够带领他尽快完成转变。
蒋慕云
绿驰研发部经理"""

ROLEPLAY_ORG_CHART_PROMPT = """请你基于设计的案例情节，提取其中所有直接、间接参与到其中的角色，并且绘制一张组织架构图，将公司的组织架构梳理清晰，案例中所有的角色要在组织架构图中对应的位置体现。

# 输出要求
1. 组织架构图必须包含该企业的多有部门，不能仅仅是案例中所涉及的部门和角色；
2. 仅仅输出组织架构图本身，不需要包含任何其他信息；
3. 组织架构图中，涉及到案例中的人物，请标记姓名，没有的不需要标注任何其他信息"""

ROLEPLAY_SUBORDINATE_ROLE_PROMPT = """你是人力资源部专家，现在你需要撰写一份员工的信息，通过邮件的方式发给其上级。

员工：{subordinate_role}
上级：{superior_role}

# 要求
1. 性格尽量鲜明，且不好管理
2. 材料中包含360评估结果，能够体现其能力方面的特征，以数据的形式呈现
3. 包含最近一次的绩效谈话结果（包括绩效结果、阶段复盘、需要提升、员工本人的看法），绩效的结果并不好
4. 字数：1500字左右

# 输出格式与示例
标题：概括邮件内容的标题
发信人 ： 刘远@lvchi.com
收信人 ： 您@lvchi.com
主题：关于李明月的介绍
陈经理：
您好，欢迎您加入绿驰，希望在您的带领下，我们的业务能更上一层楼。应您的要求，现向您介绍一些人力资源部核心骨干员工的情况。
李明月个人信息
姓名： 李明月	岗位：HRBP（研发）
年龄：35岁	司龄：3年
岗位职责
结合公司业务发展需求，与业务单元紧密合作，落地公司人力资源政策，提供针对性的人力资源解决方案，包含招聘与配置、人才培养与发展、薪酬绩效、员工关系等。
当前阶段，招聘是李明月的工作重点：
1. 招聘规划：结合业务需求制定招聘规划。根据行业趋势和岗位特点，建议用人标准调整（如薪资范围、灵活要求等）。
2. 渠道开发与管理：发布职位信息到招聘网站（如猎聘、智联）、社交媒体或内部系统。开拓多样化招聘渠道（校招、猎头、内推、行业论坛等），优化渠道效果。在此基础上，建立行业人才地图和外部人才库。
3. 候选人筛选、沟通与面试流程管理：根据简历、岗位要求快速识别匹配度高的候选人。评估候选人基本素质、求职动机和文化适配性。安排面试时间、场地，协调面试官（如业务部门负责人、高管）进行面试。跟进面试反馈，汇总评价并推进下一轮流程。
4. 背景调查与录用：对拟录用候选人进行背调（学历、工作经历、信用记录等）。
5. 薪资谈判：根据企业薪酬体系与候选人协商薪资福利。发放录用通知书（Offer），跟进入职材料准备（如体检、合同签订）。
个人情况简要介绍
6. 专业经验：是汽车行业的HR老兵，具有多个模块的丰富经验，包括招聘、薪酬福利、员工关系等。
7. 个人特征：认真负责，小心谨慎，注重规则、流程和效率，缺乏创新性，倾向于独立完成任务，不喜欢被外界干扰或改变自己的工作方式。沟通方式直截了当，不会拐弯抹角。
主要优势
1. 严肃、细致、谨慎：是一个注重细节、认真负责的人，严格遵循规则和流程做事；
2. 有执行力：推进工作能够一丝不苟，严格按照计划执行，注重任务的时间节点，能够很好地评估风险。
需要改进的关键领域
3. 工作中缺少创新和变革 ：在人力资源组织的转型中，对新事物的接受度不高，比较依赖于个人已经习惯的做法，习惯按照确定的流程和规范做有把握的事情，不愿意冒险，较少主动探索新的方式和方法；
4. 处理事情缺少灵活性：习惯按照人力资源的各项政策来开展工作，有原则性，但是缺少应对矛盾的灵活性；
5. 与团队的融合不够：与团队之间相处并不是很融洽，同事认为他不太愿意把资源分享出来。
蒋慕云
人力资源部经理"""

ROLEPLAY_BOOK_ASSEMBLY_PROMPT = """你是一个案例开发专家，现在需要将案例中各个片段拼接好，不要做任何增删，把所有内容原样拼接。"""

ROLEPLAY_SIMULATION_CHECK_PROMPT = """你是一个考生，你现在正在面临一个测验，即上下级角色扮演模拟演练，现在请你带入自己的角色，详细阅读题本内容，然后找出你感到有歧义、不理解的地方。

# 输入
题本内容：{book_content}
你的角色是题本中的上级角色

# 模拟要求
1. 你需要通篇阅读题本
2. 你需要评估自己对题本给的任务和目标是否清晰
3. 你需要发现题本中让你感到困惑的地方有哪些

# 输出内容和要求
输出内容：任务明确与否、上下文一致与否
输出要求：字数不超过1500字"""

ROLEPLAY_OPTIMIZATION_SUGGESTION_PROMPT = """你是一个题本优化专家，现在我有一套角色扮演题本，经过了考生模拟测试，测试的结果反馈到你这里，你需要基于此来反馈题本是否需要优化，以及优化的建议是什么。

# 输入
考生模拟测试反馈：{simulation_feedback}

# 评审要求
请基于考生模拟测试反馈的内容，对一下信息进行二次判断：
1. 任务明确性：考生理解的题本任务是否明确，是否完全知道自己要做什么，达到什么目的
2. 信息一致性：题本中是否有一些信息不一致、逻辑不一致的地方，如果有请指出

# 提出建议要求
提出的修改建议，原则要本着最小修改原则，即尽量不调整的原有内容的基础上，做最微小的调整
# 输出要求
1. 任务明确性
2. 信息一致性
3. 修改建议"""

ROLEPLAY_BOOK_OPTIMIZATION_PROMPT = """你是一个题本优化专家，现在我有一套角色扮演题本，经过了考生模拟测试和专家复核，优化建议反馈到你这里，你需要基于此对题本进行优化。

# 输入
题本内容：{book_content}
优化建议：{optimization_suggestion}

# 优化要求
1. 遵循最小修改原则，不要对题本进行大规模修改，只能做小修小改
2. 不改变原有的题本内容结构
3. 输出的题本内容字数基本和修改前相差不差过300字

# 输出
输出优化后的题本内容"""


class RolePlayWorkflow:
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
            SystemMessage(content=ROLEPLAY_LEVEL_DUTIES_PROMPT.format(level=level)),
            HumanMessage(content="请生成管理层级职责")
        ])
        level_duties = (await (level_duties_prompt | self.llm).ainvoke({})).content
        
        # Step 2: 考察工具挑战点设计 (198460)
        challenge_design_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_CHALLENGE_DESIGN_PROMPT.format(abilities=abilities)),
            HumanMessage(content="请设计挑战点")
        ])
        challenge_points = (await (challenge_design_prompt | self.llm).ainvoke({})).content
        
        # Step 3: 条件分支 - 检查是否有背景材料
        if not background_material or background_material.strip() == "":
            # 生成默认冲突场景（模拟Coze中155555节点）
            generate_conflict_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=ROLEPLAY_GENERATE_CONFLICT_SCENARIOS_PROMPT),
                HumanMessage(content="请生成企业沟通冲突场景")
            ])
            conflict_scenarios = (await (generate_conflict_prompt | self.llm).ainvoke({})).content
        else:
            # 从用户提供的背景材料提取冲突场景（模拟Coze中112399批处理节点）
            extract_conflict_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=ROLEPLAY_EXTRACT_CONFLICT_FROM_FILE_PROMPT.format(background_material=background_material)),
                HumanMessage(content="请提取冲突场景")
            ])
            conflict_scenarios = (await (extract_conflict_prompt | self.llm).ainvoke({})).content
        
        # Step 4: 核心场景选择 (197594)
        core_scene_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_CORE_SCENE_SELECTION_PROMPT.format(
                challenge_points=challenge_points,
                conflict_scenarios=conflict_scenarios,
                level_duties=level_duties
            )),
            HumanMessage(content="请选择核心场景")
        ])
        core_scenes = (await (core_scene_prompt | self.llm).ainvoke({})).content
        
        # Step 5: 角色与任务设计 (148369)
        role_task_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_ROLE_TASK_DESIGN_PROMPT.format(level=level)),
            HumanMessage(content=f"请设计角色与任务，场景：{core_scenes}")
        ])
        role_task = (await (role_task_prompt | self.llm).ainvoke({})).content
        
        # Step 6: 冲突场景扩写 (190041)
        conflict_expand_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_CONFLICT_EXPAND_PROMPT.format(
                background=role_task,
                scenarios=core_scenes
            )),
            HumanMessage(content="请扩写冲突场景")
        ])
        conflict_expanded = (await (conflict_expand_prompt | self.llm).ainvoke({})).content
        
        # Step 7: 冲突场景编排 (1463124) - 邮件格式
        conflict_layout_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_CONFLICT编排_PROMPT.format(
                background=role_task,
                scenarios=conflict_expanded
            )),
            HumanMessage(content="请编排邮件格式冲突场景")
        ])
        conflict_emails = (await (conflict_layout_prompt | self.llm).ainvoke({})).content
        
        # Step 8: 组织架构图生成 (131995) 和 下级角色生成 (121587) - 并行
        org_chart_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_ORG_CHART_PROMPT),
            HumanMessage(content=f"请生成组织架构图，案例内容：{role_task}{conflict_emails}")
        ])
        org_chart = (await (org_chart_prompt | self.llm).ainvoke({})).content
        
        subordinate_role_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_SUBORDINATE_ROLE_PROMPT.format(
                subordinate_role="下级角色",
                superior_role="上级角色"
            )),
            HumanMessage(content=f"请生成下级角色，角色：{role_task}，业务表现：{conflict_emails}")
        ])
        subordinate_role = (await (subordinate_role_prompt | self.llm).ainvoke({})).content
        
        # Step 9: 题本拼接 (188681)
        assembly_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_BOOK_ASSEMBLY_PROMPT),
            HumanMessage(content=f"请拼接题本：{role_task} + {subordinate_role} + {org_chart} + {conflict_emails}")
        ])
        book_assembled = (await (assembly_prompt | self.llm).ainvoke({})).content
        
        # Step 10: 考生模拟校验 (116459)
        simulation_check_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_SIMULATION_CHECK_PROMPT.format(book_content=book_assembled)),
            HumanMessage(content="请进行考生模拟校验")
        ])
        simulation_result = (await (simulation_check_prompt | self.llm).ainvoke({})).content
        
        # Step 11: 优化建议 (155140)
        optimization_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_OPTIMIZATION_SUGGESTION_PROMPT.format(simulation_feedback=simulation_result)),
            HumanMessage(content="请提供优化建议")
        ])
        optimization_suggestion = (await (optimization_prompt | self.llm).ainvoke({})).content
        
        # Step 12: 题本优化 (151313) - 最终输出
        final_optimization_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ROLEPLAY_BOOK_OPTIMIZATION_PROMPT.format(
                book_content=book_assembled,
                optimization_suggestion=optimization_suggestion
            )),
            HumanMessage(content="请优化题本")
        ])
        
        response = await (final_optimization_prompt | self.llm).ainvoke({})
        
        # 构建元信息
        meta = QuestionnaireMeta(
            tool_id="roleplay",
            tool_name="角色扮演",
            level=level,
            duration=30,
            generated_at=datetime.now().isoformat()
        )
        
        # 从文本输出中提取角色信息
        text_output = response.content
        
        # 尝试从输出中提取关键信息
        role_info = None
        scenario = None
        
        # 简单的解析（实际可能需要更复杂的逻辑）
        if "李明月" in text_output:
            role_info = RoleInfo(
                subordinate_name="李明月",
                position="HRBP（研发）",
                background="研发部门HRBP，负责招聘和员工关系工作",
                personality="认真负责，但有时过于坚持原则，缺乏灵活性"
            )
        
        if "谈话" in text_output or "沟通" in text_output:
            scenario = "关于近期招聘和员工绩效管理的问题沟通"
        
        content = QuestionnaireContent(
            role_info=role_info,
            scenario=scenario or text_output[:500] if text_output else "角色扮演场景"
        )
        
        schema = QuestionnaireSchema(meta=meta, content=content)
        return schema.to_json_string()