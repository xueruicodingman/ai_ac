from typing import List, Dict, Any
from src.services.ai_service import AIService
from src.workflows.handbook_workflow import HandbookWorkflow

class HandbookService(AIService):
    def __init__(self, api_key: str, model: str = None, api_url: str = None):
        super().__init__(api_key, model, api_url)
        self.workflow = HandbookWorkflow(self.llm)
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        questionnaires: List[Dict[str, str]]
    ) -> str:
        return await self.workflow.generate(
            competency_model=competency_model,
            evaluation_matrix=evaluation_matrix,
            questionnaires=questionnaires
        )
