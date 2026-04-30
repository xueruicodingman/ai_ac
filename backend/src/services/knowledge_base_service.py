import re
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from src.models.knowledge_base import KnowledgeBase
from src.config import settings

class KnowledgeBaseService:
    def __init__(self, db: AsyncSession, user_id: int, api_key: str = None, model: str = None, api_url: str = None):
        from src.config import settings
        self.db = db
        self.user_id = user_id
        self.api_key = api_key
        self.model = model
        self.api_url = api_url

    def _get_llm(self):
        from src.config import settings
        return ChatOpenAI(
            api_key=self.api_key or settings.API_KEY,
            base_url=self.api_url or settings.DEFAULT_API_URL,
            model=self.model or settings.DEFAULT_MODEL,
            temperature=0.1
        )

    async def get_knowledge_base(self, tool: str) -> Optional[Dict[str, Any]]:
        """获取知识库"""
        result = await self.db.execute(
            select(KnowledgeBase).where(
                and_(
                    KnowledgeBase.user_id == self.user_id,
                    KnowledgeBase.tool == tool
                )
            )
        )
        kb = result.scalar_one_or_none()
        if not kb:
            return None
        return {
            "tool": kb.tool,
            "chunk_config": json.loads(kb.chunk_config) if kb.chunk_config else {},
            "chunks": json.loads(kb.chunks) if kb.chunks else [],
            "source_documents": json.loads(kb.source_documents) if kb.source_documents else []
        }

    async def create_or_update_knowledge_base(
        self,
        tool: str,
        chunk_config: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        source_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建或更新知识库"""
        result = await self.db.execute(
            select(KnowledgeBase).where(
                and_(
                    KnowledgeBase.user_id == self.user_id,
                    KnowledgeBase.tool == tool
                )
            )
        )
        kb = result.scalar_one_or_none()

        if kb:
            kb.chunk_config = json.dumps(chunk_config, ensure_ascii=False)
            kb.chunks = json.dumps(chunks, ensure_ascii=False)
            kb.source_documents = json.dumps(source_documents, ensure_ascii=False)
        else:
            kb = KnowledgeBase(
                user_id=self.user_id,
                tool=tool,
                chunk_config=json.dumps(chunk_config, ensure_ascii=False),
                chunks=json.dumps(chunks, ensure_ascii=False),
                source_documents=json.dumps(source_documents, ensure_ascii=False)
            )
            self.db.add(kb)

        await self.db.commit()
        await self.db.refresh(kb)

        return {
            "tool": kb.tool,
            "chunk_config": chunk_config,
            "chunks": chunks,
            "source_documents": source_documents
        }

    async def upload_document(
        self,
        tool: str,
        file_name: str,
        file_content: str,
        chunk_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """上传文档并切片"""
        kb = await self._get_or_create_kb(tool)

        if chunk_config.get("strategy") == "semantic":
            chunks = await self.chunk_text_semantic(file_content, chunk_config)
        else:
            chunks = self.chunk_text(file_content, chunk_config)

        source_documents = json.loads(kb.source_documents) if kb.source_documents else []
        source_documents.append({
            "id": uuid.uuid4().hex[:8],
            "name": file_name,
            "size": len(file_content),
            "content": file_content,
            "uploaded_at": datetime.utcnow().isoformat()
        })

        kb.chunk_config = json.dumps(chunk_config, ensure_ascii=False)
        kb.chunks = json.dumps(chunks, ensure_ascii=False)
        kb.source_documents = json.dumps(source_documents, ensure_ascii=False)
        await self.db.commit()

        return {
            "tool": tool,
            "chunk_config": chunk_config,
            "chunks": chunks,
            "source_documents": source_documents
        }

    async def update_chunks(self, tool: str, chunk_config: Dict[str, Any]) -> Dict[str, Any]:
        """更新切片配置并重新切片"""
        kb = await self._get_or_create_kb(tool)

        source_documents = json.loads(kb.source_documents) if kb.source_documents else []
        all_content = "\n\n".join(doc.get("content", "") for doc in source_documents if doc.get("content"))

        if not all_content:
            chunks = []
        elif chunk_config.get("strategy") == "semantic":
            chunks = await self.chunk_text_semantic(all_content, chunk_config)
        else:
            chunks = self.chunk_text(all_content, chunk_config)

        kb.chunk_config = json.dumps(chunk_config, ensure_ascii=False)
        kb.chunks = json.dumps(chunks, ensure_ascii=False)
        await self.db.commit()

        return {"chunks": chunks, "chunk_config": chunk_config}

    async def use_handbook_as_source(
        self,
        tool: str,
        chunk_config: Dict[str, Any],
        handbook_content: str
    ) -> Dict[str, Any]:
        """使用评委手册内容作为知识库"""
        if chunk_config.get("strategy") == "semantic":
            chunks = await self.chunk_text_semantic(handbook_content, chunk_config)
        else:
            chunks = self.chunk_text(handbook_content, chunk_config)

        source_documents = [{
            "id": uuid.uuid4().hex[:8],
            "name": "评委手册",
            "size": len(handbook_content),
            "content": handbook_content,
            "source": "handbook",
            "uploaded_at": datetime.utcnow().isoformat()
        }]

        return await self.create_or_update_knowledge_base(tool, chunk_config, chunks, source_documents)

    async def delete_knowledge_base(self, tool: str) -> bool:
        """删除知识库"""
        result = await self.db.execute(
            select(KnowledgeBase).where(
                and_(
                    KnowledgeBase.user_id == self.user_id,
                    KnowledgeBase.tool == tool
                )
            )
        )
        kb = result.scalar_one_or_none()

        if kb:
            await self.db.delete(kb)
            await self.db.commit()
            return True
        return False

    async def _get_or_create_kb(self, tool: str) -> KnowledgeBase:
        """获取或创建知识库记录"""
        result = await self.db.execute(
            select(KnowledgeBase).where(
                and_(
                    KnowledgeBase.user_id == self.user_id,
                    KnowledgeBase.tool == tool
                )
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            kb = KnowledgeBase(
                user_id=self.user_id,
                tool=tool,
                chunk_config="{}",
                chunks="[]",
                source_documents="[]"
            )
            self.db.add(kb)
            await self.db.commit()
            await self.db.refresh(kb)

        return kb

    def chunk_text(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据策略切片"""
        strategy = config.get("strategy", "heading")
        separator = config.get("separator", "##")
        max_length = config.get("max_length", 500)

        if not content:
            return []

        if strategy == "semantic":
            return []  # 语义切片需要异步调用
        elif strategy == "paragraph":
            return self._chunk_by_paragraph(content, separator, max_length)
        else:
            return self._chunk_by_heading(content, separator, max_length)

    async def chunk_text_semantic(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """语义切片 - 调用 LLM 智能识别语义边界"""
        max_length = config.get("max_length", 500)

        if not content:
            return []

        system_prompt = """你是一个专业的文档切片助手。你的任务是将长文档切分成语义完整的片段。

请分析文档内容，识别语义边界，将文档切分成若干个语义完整的片段。每个片段应该：
1. 主题集中，不要混入不相关内容
2. 长度适中（一般 300-800 字）
3. 有清晰的语义边界

请以 JSON 格式返回切片结果，格式如下：
{
  "chunks": [
    {
      "title": "片段标题（概括本段主题）",
      "content": "片段内容（完整的一段话）",
      "keywords": ["关键词1", "关键词2", "关键词3"]
    }
  ]
}

注意：
- title 应该简洁明了，概括本段主题
- content 应该语义完整，是一段完整的话
- keywords 应该从本段内容中提取 2-4 个关键词"""

        user_prompt = f"请将以下文档进行语义切片：\n\n{content}"

        llm = self._get_llm()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = await llm.ainvoke(messages)
            result_text = response.content if hasattr(response, 'content') else str(response)

            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            result = json.loads(result_text.strip())

            chunks = result.get("chunks", [])
            for chunk in chunks:
                chunk["id"] = uuid.uuid4().hex[:8]

            return chunks

        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}, response: {response.content if hasattr(response, 'content') else response}")
            return [{
                "id": uuid.uuid4().hex[:8],
                "title": "全文",
                "content": content[:max_length],
                "keywords": self._extract_keywords(content)
            }]
        except Exception as e:
            print(f"语义切片失败: {e}")
            return [{
                "id": uuid.uuid4().hex[:8],
                "title": "全文",
                "content": content[:max_length],
                "keywords": self._extract_keywords(content)
            }]

    def _chunk_by_heading(self, content: str, separator: str, max_length: int) -> List[Dict[str, Any]]:
        """按标题切片"""
        chunks = []
        pattern = rf'({re.escape(separator)} [^\n]+)\n?(.*?)(?={re.escape(separator)} |$)'

        for i, match in enumerate(re.finditer(pattern, content, re.DOTALL)):
            title = match.group(1).strip()
            body = match.group(2).strip()
            chunks.append({
                "id": uuid.uuid4().hex[:8],
                "title": title,
                "content": body[:max_length],
                "keywords": self._extract_keywords(body)
            })

        if not chunks and len(content) > 10:
            chunks.append({
                "id": uuid.uuid4().hex[:8],
                "title": "全文",
                "content": content[:max_length],
                "keywords": self._extract_keywords(content)
            })

        return chunks

    def _chunk_by_paragraph(self, content: str, separator: str, max_length: int) -> List[Dict[str, Any]]:
        """按段落切片"""
        chunks = []
        paragraphs = content.split(separator if separator != '##' else '\n\n')

        current_chunk = ""
        current_title = "段落 1"

        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= max_length:
                current_chunk += para + separator
            else:
                if current_chunk:
                    chunks.append({
                        "id": uuid.uuid4().hex[:8],
                        "title": current_title,
                        "content": current_chunk.strip()[:max_length],
                        "keywords": self._extract_keywords(current_chunk)
                    })
                current_chunk = para + separator
                current_title = f"段落 {i + 1}"

        if current_chunk:
            chunks.append({
                "id": uuid.uuid4().hex[:8],
                "title": current_title,
                "content": current_chunk.strip()[:max_length],
                "keywords": self._extract_keywords(current_chunk)
            })

        return chunks

    def _chunk_by_sentence(self, content: str, separator: str, max_length: int) -> List[Dict[str, Any]]:
        """按句子切片"""
        import re as re_module
        chunks = []

        sentence_endings = '。！？!？.'
        pattern = rf'([^{sentence_endings}]+[{sentence_endings}])'

        sentences = re_module.findall(pattern, content)
        current_chunk = ""
        chunk_num = 1

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append({
                        "id": uuid.uuid4().hex[:8],
                        "title": f"句段 {chunk_num}",
                        "content": current_chunk.strip(),
                        "keywords": self._extract_keywords(current_chunk)
                    })
                    chunk_num += 1
                current_chunk = sentence

        if current_chunk:
            chunks.append({
                "id": uuid.uuid4().hex[:8],
                "title": f"句段 {chunk_num}",
                "content": current_chunk.strip(),
                "keywords": self._extract_keywords(current_chunk)
            })

        return chunks

    def _chunk_by_keyword(self, content: str, separator: str, max_length: int) -> List[Dict[str, Any]]:
        """按关键词切片"""
        chunks = []
        keywords = ['考点：', '冲突：', '考察点：', '情境：', '问题：']

        pattern = '|'.join(re.escape(kw) for kw in keywords)
        parts = re.split(pattern, content)

        current_chunk = ""
        chunk_num = 1

        for i, part in enumerate(parts):
            if i == 0:
                current_chunk = part
            else:
                keyword = keywords[[re.search(kw, content[sum(len(p) for p in parts[:i]):]) for kw in keywords if kw in content[sum(len(p) for p in parts[:i]):]]][0] if any(kw in content[sum(len(p) for p in parts[:i]):] for kw in keywords) else keywords[0]
                if current_chunk:
                    chunks.append({
                        "id": uuid.uuid4().hex[:8],
                        "title": f"知识点 {chunk_num}",
                        "content": current_chunk.strip()[:max_length],
                        "keywords": self._extract_keywords(current_chunk)
                    })
                    chunk_num += 1
                current_chunk = keyword + part

        if current_chunk:
            chunks.append({
                "id": uuid.uuid4().hex[:8],
                "title": f"知识点 {chunk_num}",
                "content": current_chunk.strip()[:max_length],
                "keywords": self._extract_keywords(current_chunk)
            })

        return chunks

    def _chunk_by_fixed_length(self, content: str, max_length: int) -> List[Dict[str, Any]]:
        """固定字数切片"""
        chunks = []
        start = 0
        chunk_num = 1

        while start < len(content):
            end = start + max_length
            chunk_content = content[start:end]

            title = f"片段 {chunk_num}"

            if start + max_length < len(content) and end < len(content):
                break_point = chunk_content.rfind('。')
                if break_point > max_length * 0.5:
                    chunk_content = chunk_content[:break_point + 1]
                    end = start + break_point + 1

            chunks.append({
                "id": uuid.uuid4().hex[:8],
                "title": title,
                "content": chunk_content.strip(),
                "keywords": self._extract_keywords(chunk_content)
            })

            start = end
            chunk_num += 1

        return chunks

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        patterns = [r'考察点[：:]([^\n]+)', r'考点[：:]([^\n]+)', r'冲突[：:]([^\n]+)']
        keywords = []
        for pattern in patterns:
            keywords.extend(re.findall(pattern, text)[:3])
        return keywords[:5]

    async def update_chunk_content(
        self,
        tool: str,
        chunk_id: str,
        chunk_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新单个切片的内容"""
        kb = await self._get_or_create_kb(tool)

        chunks = json.loads(kb.chunks) if kb.chunks else []

        for i, chunk in enumerate(chunks):
            if chunk.get("id") == chunk_id:
                chunks[i] = {
                    "id": chunk_id,
                    "title": chunk_data.get("title", chunk.get("title", "")),
                    "content": chunk_data.get("content", chunk.get("content", "")),
                    "keywords": chunk_data.get("keywords", chunk.get("keywords", []))
                }
                break

        kb.chunks = json.dumps(chunks, ensure_ascii=False)
        await self.db.commit()

        return {"chunks": chunks}

    async def delete_chunk(self, tool: str, chunk_id: str) -> Dict[str, Any]:
        """删除单个切片"""
        kb = await self._get_or_create_kb(tool)

        chunks = json.loads(kb.chunks) if kb.chunks else []
        chunks = [c for c in chunks if c.get("id") != chunk_id]
        kb.chunks = json.dumps(chunks, ensure_ascii=False)
        await self.db.commit()

        return {"chunks": chunks}

    async def add_chunk(self, tool: str, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """新增切片"""
        kb = await self._get_or_create_kb(tool)

        chunks = json.loads(kb.chunks) if kb.chunks else []
        new_chunk = {
            "id": uuid.uuid4().hex[:8],
            "title": chunk_data.get("title", "新切片"),
            "content": chunk_data.get("content", ""),
            "keywords": chunk_data.get("keywords", [])
        }
        chunks.append(new_chunk)
        kb.chunks = json.dumps(chunks, ensure_ascii=False)
        await self.db.commit()

        return {"chunks": chunks}