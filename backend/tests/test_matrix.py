import pytest
from src.workflows.matrix_workflow import TOOLS

def test_default_tools():
    assert len(TOOLS) == 5
    tool_ids = [t["id"] for t in TOOLS]
    assert "beh" in tool_ids
    assert "lgd" in tool_ids
    assert "roleplay" in tool_ids
    assert "case" in tool_ids
    assert "vision" in tool_ids

def test_tool_info():
    from src.services.questionnaire_service import QuestionnaireService
    
    service = QuestionnaireService(api_key="test")
    all_tools = service.get_all_tools()
    
    assert len(all_tools) == 5
    assert all_tools["beh"]["name"] == "BEI行为事件访谈"
