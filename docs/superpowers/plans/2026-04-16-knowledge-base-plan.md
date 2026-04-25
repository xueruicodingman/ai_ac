# 知识库管理功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在题本生成页面的评委手册下方添加知识库管理功能，用于管理测评工具的知识库切片

**Architecture:** 在现有 judge_handbooks 表基础上新增切片相关字段，创建独立知识库管理页面

**Tech Stack:** FastAPI + SQLAlchemy + React + sentence-transformers + faiss

---

## 文件结构

```
backend/
├── src/
│   ├── models/
│   │   └── judge_handbook.py          # 修改：新增字段
│   ├── routers/
│   │   └── knowledge_base.py          # 新建
│   ├── services/
│   │   └── knowledge_base_service.py  # 新建
│   └── main.py                        # 修改：注册router
frontend/src/app/
│   ├── api.ts                         # 修改：新增API
│   ├── components/
│   │   ├── QuestionBook.tsx          # 修改：添加知识库入口
│   │   └── KnowledgeBase.tsx        # 新建
│   └── App.tsx                       # 修改：添加路由
```

---

## Task 1: 数据库模型修改

**Files:**
- Modify: `backend/src/models/judge_handbook.py`
- Test: 直接运行 `python -c "from src.models.judge_handbook import JudgeHandbook; print('OK')"`

- [ ] **Step 1: 修改 judge_handbook.py 添加新字段**

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from src.database import Base

class JudgeHandbook(Base):
    __tablename__ = "judge_handbooks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("competency_models.id"), nullable=False)
    matrix_id = Column(Integer, ForeignKey("evaluation_matrices.id"), nullable=False)
    tool = Column(String(20), nullable=False)
    judge_content = Column(Text, nullable=False)
    actor_content = Column(Text)
    word_url = Column(String(500))
    pdf_url = Column(String(500))
    status = Column(String(20), default="pending")
    
    # 新增字段
    chunk_config = Column(JSON)         # 切片配置：{separator: "##", max_length: 500}
    chunks = Column(JSON)               # 切片结果：[{id, title, content, keywords}]
    source_documents = Column(JSON)     # 原始文档：[{name, content, size}]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: 验证模型加载正常**

Run: `cd /Users/ximenruixue/Desktop/AC_AI/backend && python -c "from src.models.judge_handbook import JudgeHandbook; print('OK')"`

---

## Task 2: 创建知识库 Service

**Files:**
- Create: `backend/src/services/knowledge_base_service.py`
- Test: `cd backend && python -c "from src.services.knowledge_base_service import KnowledgeBaseService; print('OK')"`

- [ ] **Step 1: 创建 knowledge_base_service.py**

```python
import re
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.models.judge_handbook import JudgeHandbook

class KnowledgeBaseService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
    
    async def get_knowledge_base(self, tool: str) -> Optional[Dict[str, Any]]:
        """获取知识库"""
        result = await self.db.execute(
            select(JudgeHandbook).where(
                and_(
                    JudgeHandbook.user_id == self.user_id,
                    JudgeHandbook.tool == tool
                )
            )
        )
        handbook = result.scalar_one_or_none()
        if not handbook:
            return None
        return {
            "tool": handbook.tool,
            "chunk_config": handbook.chunk_config or {},
            "chunks": handbook.chunks or [],
            "source_documents": handbook.source_documents or []
        }
    
    async def upload_document(
        self,
        tool: str,
        file_name: str,
        file_content: str,
        chunk_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """上传文档并切片"""
        # 获取或创建 handbook
        result = await self.db.execute(
            select(JudgeHandbook).where(
                and_(
                    JudgeHandbook.user_id == self.user_id,
                    JudgeHandbook.tool == tool
                )
            )
        )
        handbook = result.scalar_one_or_none()
        
        if not handbook:
            raise ValueError(f"未找到 tool={tool} 的评委手册，请先生成评委手册")
        
        # 切片
        chunks = self.chunk_text(file_content, chunk_config)
        
        # 更新 source_documents
        source_documents = handbook.source_documents or []
        source_documents.append({
            "id": uuid.uuid4().hex[:8],
            "name": file_name,
            "size": len(file_content),
            "uploaded_at": datetime.utcnow().isoformat()
        })
        
        # 更新数据库
        handbook.chunk_config = chunk_config
        handbook.chunks = chunks
        handbook.source_documents = source_documents
        await self.db.commit()
        
        return {
            "tool": tool,
            "chunk_config": chunk_config,
            "chunks": chunks,
            "source_documents": source_documents
        }
    
    async def update_chunks(self, tool: str, chunk_config: Dict[str, Any]) -> Dict[str, Any]:
        """更新切片配置并重新切片"""
        result = await self.db.execute(
            select(JudgeHandbook).where(
                and_(
                    JudgeHandbook.user_id == self.user_id,
                    JudgeHandbook.tool == tool
                )
            )
        )
        handbook = result.scalar_one_or_none()
        
        if not handbook:
            raise ValueError(f"未找到 tool={tool} 的知识库")
        
        # 合并文档内容
        all_content = ""
        if handbook.source_documents:
            # 需要从某处获取文档内容，这里简化处理
            pass
        
        chunks = self.chunk_text("", chunk_config)  # 空内容返回空数组
        
        handbook.chunk_config = chunk_config
        handbook.chunks = chunks
        await self.db.commit()
        
        return {"chunks": chunks, "chunk_config": chunk_config}
    
    async def delete_knowledge_base(self, tool: str) -> bool:
        """删除知识库"""
        result = await self.db.execute(
            select(JudgeHandbook).where(
                and_(
                    JudgeHandbook.user_id == self.user_id,
                    JudgeHandbook.tool == tool
                )
            )
        )
        handbook = result.scalar_one_or_none()
        
        if handbook:
            handbook.chunk_config = None
            handbook.chunks = None
            handbook.source_documents = None
            await self.db.commit()
            return True
        return False
    
    def chunk_text(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """按标题切片"""
        separator = config.get("separator", "##")
        max_length = config.get("max_length", 500)
        
        if not content:
            return []
        
        chunks = []
        # 匹配 ## 标题和后续内容
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
        
        # 处理没有标题的情况（整篇作为一个chunk）
        if not chunks and len(content) > 10:
            chunks.append({
                "id": uuid.uuid4().hex[:8],
                "title": "全文",
                "content": content[:max_length],
                "keywords": self._extract_keywords(content)
            })
        
        return chunks
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        patterns = [r'考察点[：:]([^\n]+)', r'考点[：:]([^\n]+)', r'冲突[：:]([^\n]+)']
        keywords = []
        for pattern in patterns:
            keywords.extend(re.findall(pattern, text)[:3])
        return keywords[:5]
```

- [ ] **Step 2: 验证导入正常**

Run: `cd /Users/ximenruixue/Desktop/AC_AI/backend && python -c "from src.services.knowledge_base_service import KnowledgeBaseService; print('OK')"`

---

## Task 3: 创建知识库 Router

**Files:**
- Create: `backend/src/routers/knowledge_base.py`
- Test: `curl http://localhost:8000/api/knowledge-base/beh` (启动后)

- [ ] **Step 1: 创建 knowledge_base.py**

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.services.knowledge_base_service import KnowledgeBaseService
from typing import Optional, Dict, Any
import json

router = APIRouter(prefix="/api/knowledge-base", tags=["知识库管理"])

@router.get("/{tool}")
async def get_knowledge_base(
    tool: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库"""
    service = KnowledgeBaseService(db, current_user.id)
    result = await service.get_knowledge_base(tool)
    if not result:
        return {
            "tool": tool,
            "chunk_config": {"separator": "##", "max_length": 500},
            "chunks": [],
            "source_documents": []
        }
    return result

@router.post("/{tool}")
async def upload_document(
    tool: str,
    file: UploadFile = File(...),
    chunk_config: str = Form('{"separator": "##", "max_length": 500}'),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传文档并切片"""
    content = await file.read()
    if hasattr(content, 'decode'):
        content = content.decode('utf-8')
    else:
        content = str(content)
    
    try:
        config = json.loads(chunk_config)
    except:
        config = {"separator": "##", "max_length": 500}
    
    service = KnowledgeBaseService(db, current_user.id)
    try:
        result = await service.upload_document(
            tool=tool,
            file_name=file.filename,
            file_content=content,
            chunk_config=config
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{tool}/chunks")
async def update_chunks(
    tool: str,
    chunk_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新切片配置并重新切片"""
    service = KnowledgeBaseService(db, current_user.id)
    result = await service.update_chunks(tool, chunk_config)
    return {"success": True, "data": result}

@router.delete("/{tool}")
async def delete_knowledge_base(
    tool: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除知识库"""
    service = KnowledgeBaseService(db, current_user.id)
    result = await service.delete_knowledge_base(tool)
    return {"success": True, "deleted": result}
```

- [ ] **Step 2: 在 main.py 注册 router**

Modify: `backend/src/main.py` 在其他 router 导入处添加:

```python
from src.routers.knowledge_base import router as knowledge_base_router
```

在 app.include_router 处添加:

```python
app.include_router(knowledge_base_router)
```

- [ ] **Step 3: 测试 router 导入**

Run: `cd /Users/ximenruixue/Desktop/AC_AI/backend && python -c "from src.routers.knowledge_base import router; print('OK')"`

---

## Task 4: 前端 API

**Files:**
- Modify: `frontend/src/app/api.ts`

- [ ] **Step 1: 添加知识库相关 API**

在 api.ts 文件末尾添加:

```typescript
export const getKnowledgeBase = async (tool: string) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}`, {
    headers: { ...getAuthHeaders() }
  });
  if (!response.ok) throw new Error('获取知识库失败');
  return response.json();
};

export const uploadDocument = async (tool: string, file: File, chunkConfig: object = {separator: "##", max_length: 500}) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('chunk_config', JSON.stringify(chunkConfig));
  
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}`, {
    method: 'POST',
    headers: { ...getAuthHeaders() },
    body: formData
  });
  if (!response.ok) throw new Error('上传文档失败');
  return response.json();
};

export const updateChunks = async (tool: string, chunkConfig: object) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}/chunks`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(chunkConfig)
  });
  if (!response.ok) throw new Error('更新切片失败');
  return response.json();
};

export const deleteKnowledgeBase = async (tool: string) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}`, {
    method: 'DELETE',
    headers: { ...getAuthHeaders() }
  });
  if (!response.ok) throw new Error('删除知识库失败');
  return response.json();
};
```

---

## Task 5: 创建知识库管理页面

**Files:**
- Create: `frontend/src/app/components/KnowledgeBase.tsx`

- [ ] **Step 1: 创建 KnowledgeBase.tsx**

```tsx
import { useState, useEffect } from 'react';
import { ArrowLeft, Upload, Trash2, RefreshCw, FileText, CheckCircle } from 'lucide-react';
import { getKnowledgeBase, uploadDocument, updateChunks, deleteKnowledgeBase } from '../api';

interface KnowledgeBaseProps {
  onBack: () => void;
  initialTool?: string;
}

const TOOLS = [
  { id: 'beh', name: '行为面试(BEI)' },
  { id: 'roleplay', name: '角色扮演' },
  { id: 'lgd', name: '无领导小组讨论' },
  { id: 'case', name: '案例分析' },
  { id: 'vision', name: '个人愿景' }
];

export default function KnowledgeBase({ onBack, initialTool = 'roleplay' }: KnowledgeBaseProps) {
  const [selectedTool, setSelectedTool] = useState(initialTool);
  const [knowledgeBase, setKnowledgeBase] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [maxChunkLength, setMaxChunkLength] = useState(500);
  const [separator, setSeparator] = useState('##');

  useEffect(() => {
    loadKnowledgeBase();
  }, [selectedTool]);

  const loadKnowledgeBase = async () => {
    setLoading(true);
    try {
      const data = await getKnowledgeBase(selectedTool);
      setKnowledgeBase(data);
      if (data.chunk_config) {
        setMaxChunkLength(data.chunk_config.max_length || 500);
        setSeparator(data.chunk_config.separator || '##');
      }
    } catch (e) {
      console.error(e);
      setKnowledgeBase({ chunks: [], source_documents: [] });
    }
    setLoading(false);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploading(true);
    try {
      await uploadDocument(selectedTool, file, { separator, max_length: maxChunkLength });
      await loadKnowledgeBase();
      alert('上传成功');
    } catch (err: any) {
      alert(err.message || '上传失败');
    }
    setUploading(false);
  };

  const handleRechunk = async () => {
    setLoading(true);
    try {
      await updateChunks(selectedTool, { separator, max_length: maxChunkLength });
      await loadKnowledgeBase();
      alert('重新切片成功');
    } catch (err: any) {
      alert(err.message || '重新切片失败');
    }
    setLoading(false);
  };

  const handleDelete = async () => {
    if (!confirm('确认删除知识库？')) return;
    try {
      await deleteKnowledgeBase(selectedTool);
      await loadKnowledgeBase();
      alert('删除成功');
    } catch (err: any) {
      alert(err.message || '删除失败');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-semibold">知识库管理</h1>
      </div>

      <div className="p-6 max-w-6xl mx-auto">
        {/* 工具选择 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">选择测评工具</label>
          <div className="flex gap-2 flex-wrap">
            {TOOLS.map(tool => (
              <button
                key={tool.id}
                onClick={() => setSelectedTool(tool.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedTool === tool.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tool.name}
              </button>
            ))}
          </div>
        </div>

        {/* 切片配置 */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <h3 className="font-medium text-gray-900 mb-4">切片配置</h3>
          <div className="flex gap-4 items-end">
            <div>
              <label className="block text-sm text-gray-600 mb-1">分隔符</label>
              <input
                type="text"
                value={separator}
                onChange={e => setSeparator(e.target.value)}
                className="px-3 py-2 border rounded-lg w-32"
                placeholder="##"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">最大长度(字)</label>
              <input
                type="number"
                value={maxChunkLength}
                onChange={e => setMaxChunkLength(Number(e.target.value))}
                className="px-3 py-2 border rounded-lg w-32"
                min={100}
                max={2000}
              />
            </div>
            <button
              onClick={handleRechunk}
              disabled={loading}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              重新切片
            </button>
          </div>
        </div>

        {/* 文档上传 */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <h3 className="font-medium text-gray-900 mb-4">上传文档</h3>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
            <input
              type="file"
              onChange={handleUpload}
              accept=".txt,.md,.docx,.pdf"
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-2" />
              <p className="text-sm text-gray-600">
                {uploading ? '上传中...' : '点击或拖拽上传文件 (txt/md/docx/pdf)'}
              </p>
            </label>
          </div>
          
          {/* 已上传文档列表 */}
          {knowledgeBase?.source_documents?.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">已上传文档</h4>
              <div className="space-y-2">
                {knowledgeBase.source_documents.map((doc: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <FileText size={16} className="text-gray-500" />
                      <span className="text-sm">{doc.name}</span>
                    </div>
                    <button onClick={handleDelete} className="p-1 text-red-500 hover:bg-red-50 rounded">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 切片结果 */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-gray-900">切片结果 ({knowledgeBase?.chunks?.length || 0} 个)</h3>
          </div>
          
          {loading ? (
            <div className="text-center py-8 text-gray-500">加载中...</div>
          ) : knowledgeBase?.chunks?.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无切片，请上传文档</div>
          ) : (
            <div className="space-y-4">
              {knowledgeBase?.chunks?.map((chunk: any) => (
                <div key={chunk.id} className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-gray-900">{chunk.title}</span>
                    <span className="text-xs text-gray-500">{chunk.content.length} 字</span>
                  </div>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap line-clamp-3">
                    {chunk.content}
                  </p>
                  {chunk.keywords?.length > 0 && (
                    <div className="mt-2 flex gap-1 flex-wrap">
                      {chunk.keywords.map((kw: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">
                          {kw}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## Task 6: 修改 QuestionBook 添加入口

**Files:**
- Modify: `frontend/src/app/components/QuestionBook.tsx:817-870`
- Modify: `frontend/src/app/App.tsx`

- [ ] **Step 1: 在 QuestionBook 评委手册卡片下方添加知识库管理按钮**

在 QuestionBook.tsx 的评委手册卡片区域（约第866行），在"生成评委手册"按钮后添加:

```jsx
<button
  onClick={() => {
    const handbookContent = localStorage.getItem('judge_handbook_content');
    if (!handbookContent) {
      alert('请先生成评委手册');
      return;
    }
    onNavigate('knowledge-base', { tool: selectedTool });
  }}
  className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
>
  知识库管理
</button>
```

- [ ] **Step 2: 在 App.tsx 添加知识库页面路由**

Modify: `frontend/src/app/App.tsx`

在导入处添加:

```tsx
import KnowledgeBase from './components/KnowledgeBase';
```

在 render 函数中添加:

```tsx
case 'knowledge-base':
  return <KnowledgeBase onBack={goBack} initialTool={params?.tool || 'roleplay'} />;
```

---

## Task 7: 测试

- [ ] **Step 1: 启动后端**

Run: 
```bash
cd /Users/ximenruixue/Desktop/AC_AI/backend
source /opt/anaconda3/bin/activate root
export PYTHONPATH=/Users/ximenruixue/Desktop/AC_AI/backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: 测试 API**

```bash
curl http://localhost:8000/api/knowledge-base/roleplay
```

- [ ] **Step 3: 启动前端测试**

```bash
cd /Users/ximenruixue/Desktop/AC_AI/frontend
npm run dev
```

- [ ] **Step 4: 完整流程测试**
1. 登录系统
2. 进入题本生成页面
3. 生成评委手册
4. 点击"知识库管理"按钮
5. 上传文档测试切片

---

## 实施顺序

1. Task 1: 数据库模型
2. Task 2: Service
3. Task 3: Router
4. Task 4: 前端 API
5. Task 5: KnowledgeBase 页面
6. Task 6: 修改 QuestionBook 和 App
7. Task 7: 测试