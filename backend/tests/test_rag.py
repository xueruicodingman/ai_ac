import pytest
from src.services.roleplay_rag import RolePlayRAG


class TestRolePlayRAG:
    def test_chunk_text(self):
        rag = RolePlayRAG()
        content = """# 公司简介
公司是一家互联网科技公司。

# 角色简介
你是产品经理。

# 冲突场景一
在产品开发过程中，开发团队认为当前需求不够清晰。

# 考察点
沟通协调能力
"""
        chunks = rag.chunk_text(content)
        assert len(chunks) > 0
        assert all('content' in c for c in chunks)
        assert all('chunk_type' in c for c in chunks)

    def test_build_index(self):
        rag = RolePlayRAG()
        chunks = [{'content': '测试内容', 'chunk_type': 'test', 'keywords': [], 'text': '测试内容'}]
        rag.build_index(chunks)
        assert rag.index is not None

    def test_search_returns_empty_when_no_index(self):
        rag = RolePlayRAG()
        results = rag.search('测试查询')
        assert results == []

    def test_chunks_limit_500_chars(self):
        rag = RolePlayRAG()
        content = "# 考察点\n" + "测试内容" * 200
        chunks = rag.chunk_text(content)
        assert all(len(c['content']) <= 500 for c in chunks)