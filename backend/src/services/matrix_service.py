from typing import List, Dict, Any
from src.services.ai_service import AIService
from src.workflows.matrix_workflow import MatrixWorkflow, TOOLS

class MatrixService(AIService):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        self.workflow = MatrixWorkflow(self.llm)
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        tools: List[Dict[str, Any]] = None
    ) -> dict:
        return await self.workflow.generate(
            competency_model=competency_model,
            tools=tools
        )
    
    def get_default_tools(self) -> List[Dict[str, Any]]:
        return TOOLS
