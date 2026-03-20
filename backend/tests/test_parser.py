import pytest
from src.utils.parser import create_template_excel

def test_create_template():
    result = create_template_excel()
    assert isinstance(result, bytes)
    assert len(result) > 0
