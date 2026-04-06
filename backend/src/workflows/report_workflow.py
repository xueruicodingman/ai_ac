from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import json
import re

TEXT_TO_JSON_SYSTEM_PROMPT = """你是一个文字提取专家，你要分辨给你输入的信息是什么，可能是是一个链接，或者一套文字材料，如果是链接，就请你访问链接，然后获取文字材料，如果是文字材料，请你直接分析这些文字。
这些文字是情境模拟中的不同考生的行为记录，请你把它转化成json的数据格式。


# 输入
输入的内容为：{input}
这些文字是情境模拟中的不同考生的行为记录，一定要分析其结构，分析考生和行为的对应关系

# 文本内容
1. 文本中的字母代号，例如A1、B1、C2等，这些就是考生代号
2. 文本中的小组讨论、个人愿景、角色扮演、FBEI、案例分析等内容是模拟练习的名称
3. 文本中的内容例如学习创新、沟通协作等是能力的名称
4. 大串文字记录，例如"1. 我们协同的目标是什么，竞争力还是价格？我们有什么课题？2.有没有更具体的对策？拢一下，有没有更具体的措施3.客户分层的都在点子上，被PASS掉了4.6号提到了"，这是行为记录
# 文本对应关系
A1-小组讨论-问题解决-"1. 我们协同的目标是什么，竞争力还是价格？我们有什么课题？2.有没有更具体的对策？拢一下，有没有更具体的措施3.客户分层的都在点子上，被PASS掉了4.6号提到了"，反应的含义是：考生A1在小组讨论模拟练习中，在被考察的问题解决能力上，评委记录的行为表现内容为："1. 我们协同的目标是什么，竞争力还是价格？我们有什么课题？2.有没有更具体的对策？拢一下，有没有更具体的措施3.客户分层的都在点子上，被PASS掉了4.6号提到了"
# 输出示例
根据内容和结构按照如下的格式输出json格式：
{
    "考生代号": "A1",
    "练习名称": "小组讨论",
    "能力名称": "学习创新"，
    "行为记录": "我们协同的目标是什么，竞争力还是价格？我们有什么课题？2.有没有更具体的对策？拢一下，有没有更具体的措施3.客户分层的都在点子上，被PASS掉了4.6号提到了"
}
# 输出要求
考生代号、练习名称、能力名称、行为记录要对应好，不要对应出错。"""

TEXT_TO_JSON_HUMAN_PROMPT = "输入的内容为：{input}"

INTENT_RECOGNITION_SYSTEM_PROMPT = """你是一个意图识别专家，根据输入的report_type判断要生成哪种类型的报告。

# 输入
report_type: {report_type}

# 预设意图选项
- 组织版
- 个人版
- 反馈版

# 输出要求
直接输出匹配的意图名称，不要有其他内容。"""

ABILITY_EVAL_SYSTEM_PROMPT = """你是一个人才评估专家，你将会得到一个面试官过程不同候选人在不同面试环节的行为表现记录，你需要基于【能力评估标准】和候选人在面试环节的【行为表现】来撰写其各项能力的评价语。
【能力评估标准】
能力评估标准为：{{ability}}

请您从以上的评价标准的角度，匹配与【能力评估标准】相关联的【行为表现】，对候选人的各项能力进行评价，并且给出相应的行为依据，输出的内容示例如下：
########示例#######
【A1】
     【沟通协作】
            【评价语】：沟通不够主动，但是在应对矛盾时有较好的沟通技巧
            【行为表现】：在小组讨论中，发言不主动，比较被动，一直在等待；在FBEI中，在处理和采购沟通摄影师价格，与领导沟通压预算的事情上，不是硬碰硬，而是强调事情本身的价值，同时在非重点项上先做出让步，然后在重点项上努力争取
      【问题解决】
            【评价语】：******
            【行为表现】：********
#######示例结束########

注意：
1. 当【行为表现】不够丰富，不足以围绕【能力评估标准】给出评价语时，请在对应的【评价语】后写"未捕捉到充分的行为依据"
2. 行为不"""

ABILITY_EVAL_HUMAN_PROMPT = "输入：{input}\n{output}\n能力评估标准为：{ability}"

REPORT_REVIEW_SYSTEM_PROMPT = """你是一个人才评估专家，善于发现评价报告中的漏洞，尤其善于发现其中的逻辑漏洞。

# 输入
{{input}}

# 评价标准      
{{ability}}
# 审核原则    
从以下两个方面进行审核：
*评价语与评价标准不相关*：并没有围绕评价标准去做评价
*行为表现不能支撑评价语*：无法通过行为评价得出相应的评价语吗，或者可能也可以其他的评价
# 输出要求
1. 找到有漏洞的评价语
2. 在{{input}}的基础上进行补充标记漏洞分析部分
3. 输出中不要删减任何输入的内容
4.  输出中不要遗漏任何一个考生代号

# 输出示例
 
【候选人A1】
       【沟通协作】
                【评价语】：沟通中说话喜欢铺垫，不够简洁
                【行为表现】：在小组讨论中，发言不主动，比较被动，一直在等待；在FBEI中，在处理和采购沟通摄影师价格，与领导沟通压预算的事情上，不是硬碰硬，而是强调事情本身的价值，同时在非重点项上先做出让步，然后在重点项上努力争取
                【漏洞分析】：评价语中"沟通中说话喜欢铺垫，不够简洁"的评价，但是在能力标准中并没有"表达简洁"之类的要求，出现*评价语与评价标准不相关*漏洞
"""

REPORT_REVIEW_HUMAN_PROMPT = "输入：{input}\n评价标准：{ability}"

REPORT_OPTIMIZE_SYSTEM_PROMPT = """你是一个报告优化专家，你会基于报告出现的漏洞去对报告做优化。

# 输入
报告初稿：{{input}}
# 优化原则
1. 【定位漏洞类型】：对输入材料中【漏洞分析】进行分析，定位是以下哪一类漏洞
*评价语与评价标准不相关*：并没有围绕评价标准去做评价
*行为表现不能支撑评价语*：无法通过行为评价得出相应的评价语吗，或者可能也可以其他的评价
2. 【漏洞优化】
针对*评价语与评价标准不相关*型漏洞，优化逻辑如下：
第一步：对评价标准拆分成若干个细分标准；
第二步：分析与行为表现相关的细分标准；
第三步：围绕该细分标准重新撰写评价语；
针对*行为表现不能支撑评价语*型漏洞，优化逻辑如下：
第一步：基于行为表现提取出若干个可靠的评价结论；
第二步：提取出与评价标准相关的评价结论；
第三步：将该评价结论结论语句润色后座位最后的评价语；
3. 不改变原文结构，不做大规模的调整和修改
4.  漏洞优化后即可删除漏洞分析部分的内容，保留洽谈内容
# 输出
1. 完全按照{{input}}的结构输出，在原有文字的基础上新增、修改内容，进行一版本优化
2. 输出中不要遗漏任何一个考生代号"""

REPORT_OPTIMIZE_HUMAN_PROMPT = "报告初稿：{input}"

POTENTIAL_EVAL_SYSTEM_PROMPT = """你是一个人才评估专家，你需要通过考生的胜任力评估报告来对其进行管理潜力评估。
# 输入
输入的是考生的能力评估报告：{{input}}
# 潜力评估标准
1. 学习敏锐度
指快速从经验、信息中吸收知识、提炼规律，并灵活应用于新场景的能力。核心是 "快速迭代"—— 不仅能高效学会新技能、理解新领域，还能在陌生环境或变化中快速调整认知，将学习成果转化为实际成果，不局限于过往经验的束缚。
2. 人际敏感度
是感知、理解他人情绪、需求和行为动机的能力，以及据此灵活调整沟通方式、建立良好关系的素养。表现为能精准捕捉沟通中的潜台词，尊重他人差异，在协作、冲突处理中兼顾他人感受与目标达成，有效搭建人际连接、凝聚团队合力。
3. 自驱力
源于内在目标或兴趣的、持续推动自身前进的动力。核心是 "主动自发"—— 无需外部强督促，就能明确方向、设定高标准，在面对困难时保持韧性，主动寻求突破，不断追求自我提升和目标实现，而非满足于完成基础任务。
4. 情绪稳定性（抗压能力）
指在压力、挫折、突发状况或负面反馈面前，保持情绪平稳、心态理性的能力。关键是 "可控性"—— 不被极端情绪左右决策和行为，能快速调节心态，客观分析问题、聚焦解决方案，在高压环境中依然保持高效输出和稳定表现。
5. 思维能力
是对信息进行加工、分析、判断和构建的核心能力，核心包含两大方向：
批判性思考：不盲从权威或表面信息，能独立审视论据、识别逻辑漏洞，基于事实做出理性判断，不被固有认知或偏见束缚；
系统思考：能看到事物之间的关联与整体格局，从全局视角分析问题的根源与影响，统筹兼顾各要素，制定全面、可持续的解决方案，而非局限于局部细节。

# 输出示例
【A1】
       【人际敏感性】
              【评价语】：对他人的情绪比较敏感，能够与他人建立良好的互动关系

# 注意事项
1. 当【行为表现】不够丰富，不足以围绕【潜力评价标准】给出评价语时，请在对应的【评价语】后写"未捕捉到充分的行为依据"
2. 如果没有充分的行为依据和能力评价结果可以支撑得出任何潜力评价语，就不要在报告中体现该潜力的分析结果"""

POTENTIAL_EVAL_HUMAN_PROMPT = "输入的是考生的能力评估报告：{input}"

MANAGEMENT_SUGGESTION_SYSTEM_PROMPT = """你是一个干部管理专家，你在干部的任用方面非常专业，现在你得到一份干部评估报告，请你基于此报告给出管理发展建议。

# 输入
潜力评估报告：{{potential_report}}
能力评估报告：{{ability_report}}

# 提建议的内容和原则
使用建议：评估候选人当前适合从事的岗位和未来职业发展的方向
任用风险：评估候选人任职当前推荐岗位的风险是什么
发展建议：提出学习、培养、实践锻炼方面的发展建议
# 输出要求
使用建议：50字以内
任用风险：50字以内
发展建议：100字以内"""

MANAGEMENT_SUGGESTION_HUMAN_PROMPT = "潜力评估报告：{potential_report}\n能力评估报告：{ability_report}"

REPORT_INTEGRATE_SYSTEM_PROMPT = """你是一个报告撰写专家，请你整合两份报告。

# 输入
潜力评估报告：{{potential_report}}
能力评估报告：{{ability_report}}
管理发展建议：{{management_suggestion}}

# 整合原则
1. 按照考生编号进行内容聚合，其中A1、B1、C1等是考生的代号
2. 每个考生代号下，都有能力、潜力、管理发展建议方面的内容
3. 输出所有考生的能力、潜力、管理发展建议
4. 不改变原文内容，只按照考生代号进行聚合
5. 结构化输出，格式与标题逻辑严谨
6. 删除原报告中漏洞分析的内容

# 输出示例
包括考生编号、该考生的能力、潜力、管理发展建议
## A1
### 能力
#### 沟通协作
##### 评价语
沟通不够主动，但是在应对矛盾时有较好的沟通技巧
##### 行为表现
在小组讨论中，发言不主动，比较被动，一直在等待；在FBEI中，在处理和采购沟通摄影师价格，与领导沟通压预算的事情上，不是硬碰硬，而是强调事情本身的价值，同时在非重点项上先做出让步，然后在重点项上努力争取
#### 问题解决
##### 评价语
*************
##### 行为表现
*************
### 潜力
#### 自驱力
*************
#### 学习敏锐度
*************
### 管理发展建议
#### 使用建议
*************
#### 风险提示
*************
#### 发展建议
*************"""

REPORT_INTEGRATE_HUMAN_PROMPT = "潜力评估报告：{potential_report}\n能力评估报告：{ability_report}\n管理发展建议：{management_suggestion}"

FEEDBACK_REPORT_SYSTEM_PROMPT = """你是一个人才评估专家，你将会得到一个考生的模拟练习记录，请你基于该记录生成一份面对面的口头反馈报告。

# 输入
## 输入1：练习行为记录
考生在不同练习、不同能力上的行为表现为：{{behavior_records}}

## 输入1：能力模型
能力模型：{{ability}}

# 输出内容
1. 考生在每一项能力上的行为表现
2. 向考生反馈每一项能力的话术

# 输出要求
1. 反馈话术必须结合考生在各个练习中的行为表现
2. 反馈要尽量从正面的角度来说，本着鼓励原则，不要打击积极性
3. 反馈中尽量先说优点，再说缺点
4. 每一项能力的反馈话术不超过300字
5. 要求撰写对所有考生的所有能力的反馈话术"""

FEEDBACK_REPORT_HUMAN_PROMPT = "考生在不同练习、不同能力上的行为表现为：{behavior_records}\n能力模型：{ability}"

PERSONAL_REPORT_SYSTEM_PROMPT = """你是一名专业的人才发展顾问，擅长将组织的干部评价报告{{org_report}}，转化为面向候选人本人的发展反馈报告。请按照以下要求完成语言转换：

# 转换逻辑与标准
1. 优势部分优化：
   -保留原报告中所有优势结论及支撑案例；
   -避免空泛表扬，用"具体行为+积极结果"的结构强化说服力
2. 待改进领域转换（核心重点）：
   -禁止使用"不足""缺陷""短板""薄弱""欠缺"等负面词汇，统一替换为"待提升方向""可进一步强化的领域""发展机会点"等；
   -将"问题定性"转化为"具体行为描述"，例如：
     原表述（上级版）："决策不够果断，多次因犹豫导致项目推进滞后"→
     优化表述（候选人版）："在XX项目面临方案选择时，你对两种路径的利弊进行了细致分析，但决策周期略长，一定程度上影响了项目的推进节奏，这是可重点提升的方向"；
   -每个待提升方向后必须补充"改进逻辑+落地建议"，例如：
     针对上述决策问题补充："建议后续遇到类似场景时，可先明确核心决策标准（如：优先级、成本、风险），快速筛选出2个最优方案，通过小范围试点验证后再推进，既保证决策质量，也能提升推进效率"；
   -避免抽象指责，所有待提升点均需对应原报告中的具体案例（或合理还原案例场景），不新增未提及的问题，不夸大原有问题。
3. 评估结论优化：
   -原报告中"风险提示""上级担忧"等表述，转化为"发展潜力""提升空间"的正向引导，例如：
     原表述（上级版）："该干部在团队管理中对下属指导不足，可能影响团队稳定性"→
     优化表述（候选人版）："在团队管理中，你已具备较强的目标拆解能力，若能进一步强化对下属的个性化指导（如定期1对1沟通、明确成长路径），将更充分激发团队潜力，助力团队整体绩效提升"；
   -结论部分需强调"认可+期待"，例如："综合来看，你在XX领域已展现出扎实的专业能力和责任心，若能在待提升方向上持续发力，将进一步突破自身瓶颈，承担更重要的工作任务"。
   
4. 语言风格统一：
   -语气：温和、尊重、鼓励，避免命令式、评判式表述（如"必须""应该"可替换为"建议""不妨尝试"）；
   -句式：多用肯定句、陈述句，少用否定句；
   -词汇：选择积极、中性的词汇，例如"优化""提升""强化""完善""探索""实践"等。
    
# 输出要求
1. 无语法错误、无歧义，语言流畅自然，符合职场正式沟通场景；
2. 最终报告需让候选人感受到"被认可、被重视、被支持"，同时明确知道"哪里需要改进、如何改进"，避免产生抵触情绪或挫败感。
3. 不要使用第二人称，将自己当做第三方评估机构来撰写报告。
4. 报告中涉及多个人的评价，不同人的之间评价信息不要互相干扰

# 输出格式与样例
【综合评价】
***先生是一位*****。
但在本次测评中，也展现出一些可以更好的地方*****。
 综合评价字数限制：500字以内
【发展建议】
写1-3条
 发展建议字数限制：500字以内
【课程学习】
《课程名称1》
《课程名称2》
最多推荐2门课程
【书籍阅读】
《书籍名称1》《书籍名称2》
最多推荐2本书籍

2. 输出报告样例如下

【综合评价】
 郑之龙先生是一位目标感极强的实干者，内在驱动强，富有挑战精神。在做事方面，具备清晰的目标管理与落地能力，善于剖析问题关键，逻辑严谨，并能提出具前瞻性与实操性的创新方案，在推动技术攻坚与流程优化中展现出强烈的结果导向。在团队协作中，能主动营造讨论氛围，启发他人发言，具备良好的沟通意识与团队影响力，注重通过共识凝聚团队力量。
但在本次测评中，也展现出一些可以更好的地方。首先，口头表达中的习惯性用语较多，影响沟通的严谨性与舒适度，需提升语言表达的专业度。其次，对行业前沿动态与技术趋势的关注尚有不足，可能限制其在更高视野上的突破与发展。最后，在管理认知上，虽有担当管理与提升影响力的意愿，但系统性管理知识及团队领导、绩效管理等实操经验相对欠缺，需将业务专长转化为体系化的团队领导力。
 
【发展建议】
1.精进沟通表达，提升职业形象：需有意识地进行口头禅的刻意练习与修正，可在重要沟通前进行预演，并寻求他人反馈。建议在汇报、主持等场合，更加注重语言的精炼与专业，以增强个人表达的说服力与感染力，打造更为沉稳的领导者形象。
2.拓宽行业视野，激活创新思维：建议建立系统的行业信息获取渠道，定期跟踪软件开发领域的前沿技术、竞品动态与商业模式变革。可主动参与外部技术论坛、跨界交流，将外部趋势与内部工作相结合，避免因技术路径依赖而限制创新高度。
3.系统构建管理思维，实现从"管事"到"管人"的转变：需将管理意愿转化为系统性的学习与实践。建议从带领小型团队或项目组入手，有意识地实践目标分解、绩效反馈、人才激励与知识传承，将个人业务能力转化为可复制的团队能力，实现从技术专家到团队领导者的角色升华。
 
【课程学习】
《什么是管理者"影响力"》
《战略落地-从目标设定到执行》《新生代职场精英快速晋升21秘诀》
【书籍阅读】
《金字塔原理：思考、表达和解决问题的逻辑》《赋能：打造应对不确定性的敏捷团队》《领导梯队：全面打造领导力驱动型公司》"""

PERSONAL_REPORT_HUMAN_PROMPT = "组织版报告：{org_report}"


class ReportWorkflow:
    def __init__(self, llm):
        self.llm = llm

    def _extract_json_from_response(self, response: str) -> Any:
        content = response.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return content

    async def _recognize_intent(self, report_type: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=INTENT_RECOGNITION_SYSTEM_PROMPT.format(report_type=report_type)),
            HumanMessage(content=f"请识别意图: {report_type}")
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        result = response.content.strip()
        
        if "组织" in result:
            return "组织版"
        elif "个人" in result:
            return "个人版"
        elif "反馈" in result:
            return "反馈版"
        return result

    async def text_to_json(self, behavior_record: str) -> List[Dict[str, Any]]:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=TEXT_TO_JSON_SYSTEM_PROMPT),
            HumanMessage(content=TEXT_TO_JSON_HUMAN_PROMPT.format(input=behavior_record))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        result = self._extract_json_from_response(response.content)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
        return []

    async def evaluate_ability(
        self,
        behavior_records: List[Dict[str, Any]],
        ability_standards: List[Dict[str, Any]]
    ) -> str:
        ability_str = json.dumps(ability_standards, ensure_ascii=False, indent=2)
        
        records_text = "\n".join([
            f"考生代号: {r.get('考生代号', '')}, 练习名称: {r.get('练习名称', '')}, 能力名称: {r.get('能力名称', '')}, 行为记录: {r.get('行为记录', '')}"
            for r in behavior_records
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=ABILITY_EVAL_SYSTEM_PROMPT),
            HumanMessage(content=ABILITY_EVAL_HUMAN_PROMPT.format(input=records_text, output="", ability=ability_str))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"ability": ability_str})
        return response.content

    async def review_report(
        self,
        report_content: str,
        ability_standards: List[Dict[str, Any]]
    ) -> str:
        ability_str = json.dumps(ability_standards, ensure_ascii=False, indent=2)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=REPORT_REVIEW_SYSTEM_PROMPT),
            HumanMessage(content=REPORT_REVIEW_HUMAN_PROMPT.format(input=report_content, ability=ability_str))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"input": report_content, "ability": ability_str})
        return response.content

    async def optimize_report(self, report_content: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=REPORT_OPTIMIZE_SYSTEM_PROMPT),
            HumanMessage(content=REPORT_OPTIMIZE_HUMAN_PROMPT.format(input=report_content))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"input": report_content})
        return response.content

    async def evaluate_potential(self, ability_report: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=POTENTIAL_EVAL_SYSTEM_PROMPT),
            HumanMessage(content=POTENTIAL_EVAL_HUMAN_PROMPT.format(input=ability_report))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"input": ability_report})
        return response.content

    async def generate_management_suggestion(
        self,
        potential_report: str,
        ability_report: str
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=MANAGEMENT_SUGGESTION_SYSTEM_PROMPT),
            HumanMessage(content=MANAGEMENT_SUGGESTION_HUMAN_PROMPT.format(
                potential_report=potential_report,
                ability_report=ability_report
            ))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"potential_report": potential_report, "ability_report": ability_report})
        return response.content

    async def integrate_report(
        self,
        ability_report: str,
        potential_report: str,
        management_suggestion: str
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=REPORT_INTEGRATE_SYSTEM_PROMPT),
            HumanMessage(content=REPORT_INTEGRATE_HUMAN_PROMPT.format(
                potential_report=potential_report,
                ability_report=ability_report,
                management_suggestion=management_suggestion
            ))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"potential_report": potential_report, "ability_report": ability_report, "management_suggestion": management_suggestion})
        return response.content

    async def generate_feedback_report(
        self,
        behavior_records: List[Dict[str, Any]],
        ability_standards: List[Dict[str, Any]]
    ) -> str:
        behavior_text = "\n".join([
            f"练习名称: {r.get('练习名称', '')}, 能力名称: {r.get('能力名称', '')}, 考生代号: {r.get('考生代号', '')}, 行为记录: {r.get('行为记录', '')}"
            for r in behavior_records
        ])
        ability_str = json.dumps(ability_standards, ensure_ascii=False, indent=2)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=FEEDBACK_REPORT_SYSTEM_PROMPT),
            HumanMessage(content=FEEDBACK_REPORT_HUMAN_PROMPT.format(
                behavior_records=behavior_text,
                ability=ability_str
            ))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"behavior_records": behavior_text, "ability": ability_str})
        return response.content

    async def generate_personal_report(self, org_report: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=PERSONAL_REPORT_SYSTEM_PROMPT),
            HumanMessage(content=PERSONAL_REPORT_HUMAN_PROMPT.format(org_report=org_report))
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"org_report": org_report})
        return response.content

    async def generate_full_report(
        self,
        behavior_record: str,
        ability_standards: List[Dict[str, Any]],
        report_type: str
    ) -> Dict[str, str]:
        recognized_intent = await self._recognize_intent(report_type)
        
        behavior_records = await self.text_to_json(behavior_record)
        
        ability_report = await self.evaluate_ability(behavior_records, ability_standards)
        
        if recognized_intent == "反馈版":
            feedback_report = await self.generate_feedback_report(behavior_records, ability_standards)
            return {
                "反馈版报告": feedback_report,
                "组织版报告": ability_report
            }
        
        reviewed_report = await self.review_report(ability_report, ability_standards)
        
        optimized_report = await self.optimize_report(reviewed_report)
        
        potential_report = await self.evaluate_potential(optimized_report)
        
        management_suggestion = await self.generate_management_suggestion(
            potential_report, optimized_report
        )
        
        org_report = await self.integrate_report(
            optimized_report, potential_report, management_suggestion
        )
        
        if recognized_intent == "个人版":
            personal_report = await self.generate_personal_report(org_report)
            return {
                "个人版报告": personal_report,
                "组织版报告": org_report
            }
        
        return {
            "组织版报告": org_report
        }
