from typing import List, Dict, Any
from src.services.ai_service import AIService
from src.workflows.matrix_gen_workflow import MatrixGenWorkflow, TOOL_MAPPING

class MatrixService(AIService):
    def __init__(self, api_key: str, model: str = None, api_url: str = None):
        super().__init__(api_key, model, api_url)
        self.workflow = MatrixGenWorkflow(self.llm)
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        tools: List[Dict[str, Any]] = None,
        selected_tools: List[str] = None
    ) -> dict:
        """
        生成评估矩阵
        
        Args:
            competency_model: 胜任力模型，包含 dimensions 数组
            tools: 可选的测评工具列表（暂未使用）
            selected_tools: 用户选中的工具ID列表
        
        Returns:
            {dimension_name: [tool_id1, tool_id2, ...]}
        """
        print(f"[SERVICE] Received competency_model: {competency_model}")
        print(f"[SERVICE] Selected tools: {selected_tools}")
        
        # Handle nested structure if present
        if "competency_model" in competency_model:
            competency_model = competency_model["competency_model"]
        
        dimensions = competency_model.get("dimensions", [])
        print(f"[SERVICE] Processing {len(dimensions)} dimensions")
        
        return await self.workflow.generate(dimensions, selected_tools)
    
    def get_default_tools(self) -> List[Dict[str, Any]]:
        return [
            {"id": "beh", "name": "行为面试"},
            {"id": "lgd", "name": "无领导小组讨论"},
            {"id": "roleplay", "name": "角色扮演"},
            {"id": "vision", "name": "个人愿景"},
            {"id": "case", "name": "商业案例"},
        ]
