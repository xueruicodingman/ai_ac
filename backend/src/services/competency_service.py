from typing import List, Optional
from src.services.ai_service import AIService
from src.workflows.competency_workflow import CompetencyWorkflow

class CompetencyService(AIService):
    def __init__(self, api_key: str, model: str = None, api_url: str = None):
        super().__init__(api_key, model, api_url)
        self.workflow = CompetencyWorkflow(self.llm)
    
    async def generate(
        self,
        background: str = "",
        specified_abilities: Optional[List[str]] = None,
        num_competencies: int = 5
    ) -> dict:
        return await self.workflow.generate(
            background=background,
            specified_abilities=specified_abilities,
            num_competencies=num_competencies
        )
