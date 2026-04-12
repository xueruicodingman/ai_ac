import re
import json
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

logger = logging.getLogger(__name__)


class RolePlayRAG:
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self._model_name = model_name
        self._embedding_model = None
        self.dimension = None
        self.index = None
        self.chunks: List[Dict[str, Any]] = []
    
    @property
    def embedding_model(self):
        if self._embedding_model is None:
            try:
                logger.info(f"Loading embedding model: {self._model_name}")
                self._embedding_model = SentenceTransformer(self._model_name)
                self.dimension = self._embedding_model.get_sentence_embedding_dimension()
                logger.info(f"Embedding model loaded, dimension: {self.dimension}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return self._embedding_model
    
    def chunk_text(self, content: str) -> List[Dict[str, Any]]:
        """将题本内容分割为chunks，chunk_size < 500字"""
        chunks = []
        
        patterns = {
            'scene_background': r'# 公司简介(.*?)(?=# 角色|$)',
            'role_info': r'# 角色简介(.*?)(?=# 任务|# 冲突|$)',
            'conflict_1': r'# 冲突场景[一二1-2](.*?)(?=# 冲突|# 考察|$)',
            'conflict_2': r'# 冲突场景[一二1-2](.*?)(?=# 考察|$)',
            'challenge_point': r'# 考察点(.*?)(?=$|$)'
        }
        
        for chunk_type, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                text = match.group(1).strip()
                if len(text) > 10:
                    keywords = self._extract_keywords(text)
                    chunks.append({
                        'content': text[:500],
                        'chunk_type': chunk_type,
                        'keywords': keywords,
                        'text': text
                    })
        
        return chunks
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        important_patterns = [
            r'考察点[：:]([^\n]+)',
            r'考点[：:]([^\n]+)',
            r'冲突[：:]([^\n]+)',
            r'角色[：:]([^\n]+)'
        ]
        for pattern in important_patterns:
            matches = re.findall(pattern, text)
            keywords.extend([m.strip() for m in matches[:3]])
        return keywords[:10]
    
    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """构建FAISS索引"""
        self.chunks = chunks
        if not chunks:
            return
        
        try:
            texts = [c['content'] for c in chunks]
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            logger.info(f"Generated embeddings for {len(texts)} chunks")
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
        
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        embeddings = embeddings / norms
        
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """检索相关上下文"""
        if not self.index:
            return []
        
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        scores, indices = self.index.search(query_embedding, min(top_k, len(self.chunks)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append({
                    'chunk': self.chunks[idx],
                    'score': float(score)
                })
        return results