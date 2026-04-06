from typing import List, Optional, Dict, Any
from src.services.ai_service import AIService
from src.workflows.competency_gen_workflow import CompetencyGenWorkflow

class CompetencyService(AIService):
    def __init__(self, api_key: str, model: str = None, api_url: str = None):
        super().__init__(api_key, model, api_url)
        self.workflow = CompetencyGenWorkflow(self.llm)
    
    async def generate(
        self,
        background: str = "",
        specified_abilities: Optional[List[str]] = None,
        num_competencies: int = 5
    ) -> Dict[str, Any]:
        """
        生成胜任力模型
        
        Args:
            background: 背景材料描述
            specified_abilities: 指定的能力词条列表
            num_competencies: 生成数量（必填）
        
        Returns:
            {"dimensions": [...]}
        """
        # 确定要生成的词条列表
        competency_names = []
        
        if specified_abilities and len(specified_abilities) > 0:
            # 使用用户指定的能力词条
            competency_names = specified_abilities[:num_competencies]
        else:
            # 需要根据背景材料生成词条（暂简化为使用通用词条）
            # TODO: 后续可以增加一个单独的 LLM 调用来从背景材料中提取词条
            competency_names = self._get_default_competencies(num_competencies)
        
        # 调用工作流批量生成
        results = await self.workflow.generate(competency_names)
        
        # 转换为标准输出格式
        import uuid
        dimensions = []
        for result in results:
            dim = {
                "id": str(uuid.uuid4()),
                "name": result.get("name", ""),
                "meaning": result.get("meaning", ""),
                "behavior_criteria": []
            }
            
            for bc in result.get("behavior_criteria", []):
                dim["behavior_criteria"].append({
                    "id": str(uuid.uuid4()),
                    "title": bc.get("title", ""),
                    "description": bc.get("description", "")
                })
            
            dimensions.append(dim)
        
        return {"dimensions": dimensions}
    
    def _get_default_competencies(self, num: int) -> List[str]:
        """当没有指定能力词条时使用的默认词条"""
        defaults = [
            "问题解决", "沟通协作", "团队领导", "创新突破",
            "学习成长", "责任心", "计划执行", "逻辑思维",
            "客户导向", "决策判断"
        ]
        return defaults[:num]
