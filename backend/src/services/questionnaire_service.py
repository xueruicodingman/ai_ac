from typing import Dict, Any
from src.services.ai_service import AIService
from src.workflows.beh_workflow import BEHWorkflow
from src.workflows.lgd_workflow import LGDWorkflow
from src.workflows.roleplay_workflow import RolePlayWorkflow
from src.workflows.case_workflow import CaseWorkflow
from src.workflows.vision_workflow import VisionWorkflow

WORKFLOW_MAP = {
    "beh": BEHWorkflow,
    "lgd": LGDWorkflow,
    "roleplay": RolePlayWorkflow,
    "case": CaseWorkflow,
    "vision": VisionWorkflow
}

TOOL_INFO = {
    "beh": {"name": "BEI行为事件访谈", "duration": 60},
    "lgd": {"name": "无领导小组讨论", "duration": 90},
    "roleplay": {"name": "角色扮演", "duration": 30},
    "case": {"name": "案例分析", "duration": 90},
    "vision": {"name": "个人愿景", "duration": 30}
}

class QuestionnaireService(AIService):
    def __init__(self, api_key: str, model: str = None, api_url: str = None):
        super().__init__(api_key, model, api_url)
        self.workflows = {
            tool_id: workflow(self.llm)
            for tool_id, workflow in WORKFLOW_MAP.items()
        }
    
    async def generate(
        self,
        tool_id: str,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any]
    ) -> str:
        if tool_id not in self.workflows:
            raise ValueError(f"Unknown tool: {tool_id}")
        
        workflow = self.workflows[tool_id]
        return await workflow.generate(competency_model, evaluation_matrix)
    
    def get_tool_info(self, tool_id: str) -> Dict[str, Any]:
        return TOOL_INFO.get(tool_id, {})
    
    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        return TOOL_INFO
