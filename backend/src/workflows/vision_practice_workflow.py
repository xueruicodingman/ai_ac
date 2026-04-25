import json
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 分析用户答案 - 提取挑战应对信息
ANALYZE_ANSWER_PROMPT = """你是一个人才评估专家。请分析以下个人愿景回答，提取挑战应对的关键信息。

## 用户回答
{user_answer}

## 考察工具
{tool}

## 考察能力维度
{competencies}

## 分析要求
请从以下几个维度分析回答：

1. **战略对齐度**：回答是否与企业战略/年度重点对齐
2. **落地颗粒度**：回答是否具体到本职职责、可量化成果
3. **能力匹配度**：个人能力与岗位需求的匹配程度
4. **资源边界认知**：对资源需求和岗位职责边界的认识
5. **短期长期平衡**：近期贡献与长期发展的平衡

## 输出格式
请直接输出以下JSON格式（不要有其他内容）：
```json
{{
  "strategic_alignment": {{
    "level": "高/中/低",
    "evidence": "具体证据或分析",
    "gap": "存在的差距或不足"
  }},
  "execution_granularity": {{
    "level": "高/中/低",
    "evidence": "具体证据或分析",
    "gap": "存在的差距或不足"
  }},
  "capability_match": {{
    "level": "高/中/低",
    "evidence": "具体证据或分析",
    "gap": "存在的差距或不足"
  }},
  "resource_boundary_awareness": {{
    "level": "高/中/低",
    "evidence": "具体证据或分析",
    "gap": "存在的差距或不足"
  }},
  "time_balance": {{
    "level": "高/中/低",
    "evidence": "具体证据或分析",
    "gap": "存在的差距或不足"
  }},
  "overall_score": "1-10之间的分数",
  "key_strengths": ["优势1", "优势2"],
  "key_improvements": ["需要改进1", "需要改进2"]
}}
```"""

# 生成追问问题
GENERATE_FOLLOWUP_PROMPT = """你是一位资深人才评估面试官。请根据以下信息生成下一个追问问题。

## 当前挑战分析
{challenge_analysis}

## 挑战维度
{challenge_dimension}

## 历史回答
{previous_responses}

## 考察的胜任力
{competencies}

## 追问原则
1. 根据当前分析的薄弱环节进行追问
2. 问题要自然、简洁，不超过50字
3. 不要使用专业评估术语
4. 追问要有深度，能够进一步考察候选人的思考深度和实际能力
5. 每个挑战维度只追问1-2个最关键的问题

## 输出格式
直接输出问题内容，不要有其他格式。"""

# 生成结束语
GENERATE_COMPLETION_PROMPT = """你是一位资深人才评估专家。请基于候选人的整体表现生成结束语。

## 用户最终回答
{user_answer}

## 挑战分析汇总
{challenge_analyses}

## 考察的胜任力
{competencies}

## 结束语要求
1. 总结候选人在个人愿景规划中的核心优势和亮点
2. 指出最需要改进的关键点
3. 给出具体、可操作的改进建议
4. 语气专业、鼓励，但不虚假恭维
5. 总字数控制在200-400字

## 输出格式
直接输出结束语内容，不要有其他格式。"""

# 评估挑战应对质量的prompt
EVALUATE_CHALLENGE_RESPONSE_PROMPT = """请评估以下回答在应对特定挑战时的表现。

## 挑战类型
{challenge_type}

## 用户回答
{user_answer}

## 评估维度
1. **相关性**：回答是否针对该挑战
2. **深度**：回答是否有深度思考，而不仅仅是表面描述
3. **可操作性**：回答中的计划是否具体可执行
4. **创新性**：是否有独到的见解或创新的方法

## 输出格式
```json
{{
  "relevance": {{"score": 1-5, "reason": "..."}},
  "depth": {{"score": 1-5, "reason": "..."}},
  "actionability": {{"score": 1-5, "reason": "..."}},
  "innovation": {{"score": 1-5, "reason": "..."}},
  "overall": {{"score": 1-5, "reason": "..."}}
}}
```"""


class VisionPracticeWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def analyze_answer(
        self,
        user_answer: str,
        tool: str = "vision",
        competencies: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        分析用户答案，提取挑战应对信息
        
        Args:
            user_answer: 用户的愿景回答
            tool: 考察工具，默认vision
            competencies: 考察的胜任力列表
        
        Returns:
            Dict包含分析结果和各维度的评估
        """
        competencies_text = ""
        if competencies:
            competencies_text = "\n".join([
                f"- {c.get('name', '')}: {c.get('description', '')}"
                for c in competencies
            ])
        else:
            competencies_text = "战略思维、目标管理、执行力、学习发展"

        prompt = ChatPromptTemplate.from_template(ANALYZE_ANSWER_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = await chain.ainvoke({
                "user_answer": user_answer,
                "tool": tool,
                "competencies": competencies_text
            })
            
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            analysis = json.loads(response.strip())
            
            # 添加元数据
            analysis["analyzed_at"] = "now"
            analysis["tool"] = tool
            
            return analysis
            
        except Exception as e:
            # 返回默认分析结果
            return {
                "strategic_alignment": {
                    "level": "待评估",
                    "evidence": "分析失败",
                    "gap": "需要重新提交"
                },
                "execution_granularity": {
                    "level": "待评估",
                    "evidence": "分析失败",
                    "gap": "需要重新提交"
                },
                "capability_match": {
                    "level": "待评估",
                    "evidence": "分析失败",
                    "gap": "需要重新提交"
                },
                "resource_boundary_awareness": {
                    "level": "待评估",
                    "evidence": "分析失败",
                    "gap": "需要重新提交"
                },
                "time_balance": {
                    "level": "待评估",
                    "evidence": "分析失败",
                    "gap": "需要重新提交"
                },
                "overall_score": "待评估",
                "key_strengths": ["分析失败"],
                "key_improvements": ["请重新提交"],
                "error": str(e)
            }
    
    async def generate_followup(
        self,
        challenge: Dict[str, Any],
        previous_responses: List[str],
        competencies: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        生成追问问题
        
        Args:
            challenge: 当前挑战分析字典
            previous_responses: 历史回答列表
            competencies: 考察的胜任力列表
        
        Returns:
            追问问题字符串
        """
        competencies_text = ""
        if competencies:
            competencies_text = "\n".join([
                f"- {c.get('name', '')}: {c.get('description', '')}"
                for c in competencies
            ])
        else:
            competencies_text = "战略思维、目标管理、执行力、学习发展"
        
        previous_text = "\n".join([
            f"回答{i+1}: {resp}"
            for i, resp in enumerate(previous_responses)
        ]) if previous_responses else "暂无历史回答"
        
        # 根据challenge确定追问方向
        challenge_dimension = "战略对齐度"

        if challenge.get("strategic_alignment", {}).get("level") == "低":
            challenge_dimension = "战略对齐度"
            gap_score = 1
        elif challenge.get("execution_granularity", {}).get("level") == "低":
            challenge_dimension = "落地颗粒度"
            gap_score = 2
        elif challenge.get("capability_match", {}).get("level") == "低":
            challenge_dimension = "能力匹配度"
            gap_score = 3
        elif challenge.get("resource_boundary_awareness", {}).get("level") == "低":
            challenge_dimension = "资源边界认知"
            gap_score = 2
        elif challenge.get("time_balance", {}).get("level") == "低":
            challenge_dimension = "短期长期平衡"
            gap_score = 3
        
        prompt = ChatPromptTemplate.from_template(GENERATE_FOLLOWUP_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = await chain.ainvoke({
                "challenge_analysis": str(challenge),
                "challenge_dimension": challenge_dimension,
                "previous_responses": previous_text,
                "competencies": competencies_text
            })
            
            question = response.strip()
            # 清理可能的前缀
            question = question.lstrip("问题：").lstrip("追问：").lstrip("Q:").strip()
            
            if question and len(question) > 3:
                return question
            
            # 默认追问
            return self._get_default_followup_question(challenge_dimension)
            
        except Exception as e:
            return self._get_default_followup_question(challenge_dimension)
    
    def _get_default_followup_question(self, dimension: str) -> str:
        """根据维度返回默认追问问题"""
        default_questions = {
            "战略对齐度": "您认为您的愿景规划如何支撑公司当前的战略重点？请具体说明。",
            "落地颗粒度": "您提到的目标有什么具体的衡量标准？如何评估是否达成？",
            "能力匹配度": "您计划如何弥补当前能力与目标之间的差距？",
            "资源边界认知": "实现您的愿景需要哪些关键资源支持？",
            "短期长期平衡": "您如何平衡近期成果和长期发展的关系？"
        }
        return default_questions.get(dimension, "请具体说明您的思考过程。")
    
    async def evaluate_challenge_response(
        self,
        challenge_type: str,
        user_answer: str
    ) -> Dict[str, Any]:
        """
        评估用户在特定挑战类型下的回答质量
        
        Args:
            challenge_type: 挑战类型
            user_answer: 用户回答
        
        Returns:
            评估结果字典
        """
        prompt = ChatPromptTemplate.from_template(EVALUATE_CHALLENGE_RESPONSE_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = await chain.ainvoke({
                "challenge_type": challenge_type,
                "user_answer": user_answer
            })
            
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            evaluation = json.loads(response.strip())
            return evaluation
            
        except Exception as e:
            return {
                "relevance": {"score": 0, "reason": f"评估失败: {str(e)}"},
                "depth": {"score": 0, "reason": "评估失败"},
                "actionability": {"score": 0, "reason": "评估失败"},
                "innovation": {"score": 0, "reason": "评估失败"},
                "overall": {"score": 0, "reason": "评估失败"}
            }
    
    async def generate_completion(
        self,
        user_answer: str,
        challenge_analyses: List[Dict[str, Any]],
        competencies: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        生成结束语
        
        Args:
            user_answer: 用户最终回答
            challenge_analyses: 挑战分析列表
            competencies: 考察的胜任力列表
        
        Returns:
            结束语文本
        """
        competencies_text = ""
        if competencies:
            competencies_text = "\n".join([
                f"- {c.get('name', '')}: {c.get('description', '')}"
                for c in competencies
            ])
        else:
            competencies_text = "战略思维、目标管理、执行力、学习发展"
        
        analyses_text = "\n".join([
            f"分析{i+1}: {str(analysis)}"
            for i, analysis in enumerate(challenge_analyses)
        ]) if challenge_analyses else "暂无详细分析"
        
        prompt = ChatPromptTemplate.from_template(GENERATE_COMPLETION_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = await chain.ainvoke({
                "user_answer": user_answer,
                "challenge_analyses": analyses_text,
                "competencies": competencies_text
            })
            
            completion = response.strip()
            return completion
            
        except Exception as e:
            # 返回默认结束语
            return f"感谢您的参与。根据您的回答，您展现出对个人发展的思考。建议您在未来的规划中进一步明确战略对齐和可衡量的目标。如有任何问题，欢迎继续练习。"