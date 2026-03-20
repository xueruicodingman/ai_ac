from typing import Dict, Any, List
from src.services.ai_service import AIService
from src.workflows.report_workflow import ReportWorkflow

class ReportService(AIService):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        self.workflow = ReportWorkflow(self.llm)
    
    async def generate_feedback_report(
        self,
        name: str,
        scores: Dict[str, float],
        behaviors: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        return await self.workflow.generate_feedback_report(
            name=name,
            scores=scores,
            behaviors=behaviors or {}
        )
    
    async def generate_org_report(
        self,
        name: str,
        scores: Dict[str, float],
        feedback_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self.workflow.generate_org_report(
            name=name,
            scores=scores,
            feedback_content=feedback_content
        )
    
    async def generate_personal_report(
        self,
        name: str,
        scores: Dict[str, float],
        org_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self.workflow.generate_personal_report(
            name=name,
            scores=scores,
            org_content=org_content
        )
