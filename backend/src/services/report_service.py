from typing import Dict, Any, List
from src.services.ai_service import AIService
from src.workflows.report_workflow import ReportWorkflow

class ReportService(AIService):
    def __init__(
        self,
        api_key: str,
        model: str = None,
        api_url: str = None
    ):
        super().__init__(api_key, model, api_url)
        self.workflow = ReportWorkflow(self.llm)
    
    async def generate(self, **kwargs) -> Dict[str, Any]:
        return await self.generate_full_report(
            behavior_record=kwargs.get("behavior_record", ""),
            ability_standards=kwargs.get("ability_standards", []),
            report_type=kwargs.get("report_type", "")
        )
    
    async def generate_full_report(
        self,
        behavior_record: str,
        ability_standards: List[Dict[str, Any]],
        report_type: str
    ) -> Dict[str, Any]:
        return await self.workflow.generate_full_report(
            behavior_record=behavior_record,
            ability_standards=ability_standards,
            report_type=report_type
        )
    
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