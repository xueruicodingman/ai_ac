import pytest

def test_competency_schema_validation():
    from src.schemas.competency import BehaviorCriterion, Dimension
    
    behavior = BehaviorCriterion(
        id="test-id",
        title="自我认知",
        description="测试描述"
    )
    assert behavior.title == "自我认知"
    
    dimension = Dimension(
        id="dim-id",
        name="创新突破",
        meaning="测试含义",
        behavior_criteria=[behavior]
    )
    assert dimension.name == "创新突破"
    assert len(dimension.behavior_criteria) == 1
