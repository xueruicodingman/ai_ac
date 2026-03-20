import pytest
from src.utils.document import markdown_to_docx, generate_radar_chart

def test_markdown_to_docx():
    content = "# 测试标题\n\n这是测试内容。"
    result = markdown_to_docx(content, "测试文档")
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_generate_radar_chart():
    scores = {"领导力": 4.5, "沟通协作": 3.8, "创新能力": 4.2}
    result = generate_radar_chart(scores)
    assert isinstance(result, str)
    assert len(result) > 0
