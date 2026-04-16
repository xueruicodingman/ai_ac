# 知识库管理功能设计

## 概述

在题本生成页面的评委手册下方添加知识库管理功能，用于管理测评工具的知识库切片。

## 功能需求

1. **知识库管理入口**：评委手册卡片下方添加"知识库管理"按钮，跳转独立页面
2. **支持工具**：全部测评工具（BEI、角色扮演、LGD、案例分析、个人愿景）
3. **文档上传**：支持 txt/md/docx/pdf 格式
4. **切片配置**：按标题（##）自动切分，可配置最大chunk长度
5. **切片查看**：查看已切分的chunks内容

## 数据库设计

修改 `judge_handbooks` 表，新增字段：

```sql
ALTER TABLE judge_handbooks ADD COLUMN chunk_config JSON;
ALTER TABLE judge_handbooks ADD COLUMN chunks JSON;
ALTER TABLE judge_handbooks ADD COLUMN source_documents JSON;
```

字段说明：
- `chunk_config`: 切片配置，包含分隔符（如`##`）、最大长度（如500字）
- `chunks`: 切片结果数组，每项包含 {id, title, content, keywords}
- `source_documents`: 原始文档列表，包含文件名、路径、内容

## 后端设计

### 1. 新增 Router

`src/routers/knowledge_base.py`:

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/knowledge-base/{tool}` | GET | 获取指定工具的知识库 |
| `/api/knowledge-base/{tool}` | POST | 上传文档并自动切片 |
| `/api/knowledge-base/{tool}/chunks` | PUT | 更新切片配置并重新切片 |
| `/api/knowledge-base/{tool}` | DELETE | 删除知识库 |

### 2. Service

`src/services/knowledge_base_service.py`:

- `get_knowledge_base(db, user_id, tool)`: 获取知识库
- `upload_and_chunk(db, user_id, tool, file, config)`: 上传文档并切片
- `update_chunks(db, user_id, tool, config)`: 重新切片
- `delete_knowledge_base(db, user_id, tool)`: 删除知识库

### 3. 切片逻辑

```python
def chunk_by_headers(content: str, max_length: int = 500) -> List[Dict]:
    """按 ## 标题分割内容为chunks"""
    chunks = []
    pattern = r'(## [^#][^\n]+)\n(.*?)(?=## |$)'
    for match in re.finditer(pattern, content, re.DOTALL):
        title = match.group(1).strip()
        body = match.group(2).strip()
        chunks.append({
            "id": uuid.uuid4().hex[:8],
            "title": title,
            "content": body[:max_length],
            "keywords": extract_keywords(body)
        })
    return chunks
```

## 前端设计

### 1. QuestionBook.tsx 修改

评委手册卡片下方添加知识库管理按钮：

```jsx
<button
  onClick={() => onNavigate('knowledge-base', { tool: selectedTool })}
  className="px-4 py-2 bg-blue-600 text-white rounded-lg"
>
  知识库管理
</button>
```

### 2. 新建 KnowledgeBase.tsx

独立页面，包含：

1. **工具选择器**：切换不同测评工具
2. **文档上传区**：拖拽或点击上传
3. **切片配置**：输入最大chunk长度
4. **切片结果展示**：列表展示每个chunk，支持查看/编辑

### 3. API 调用

`frontend/src/app/api.ts` 新增：

```typescript
export const getKnowledgeBase = async (tool: string) => { ... }
export const uploadDocument = async (tool: string, file: File, config: object) => { ... }
export const updateChunks = async (tool: string, config: object) => { ... }
export const deleteKnowledgeBase = async (tool: string) => { ... }
```

## 用户流程

1. 用户在题本生成页面完成评委手册生成
2. 点击"知识库管理"按钮，跳转知识库页面
3. 选择测评工具，上传文档
4. 系统自动按标题切片，展示结果
5. 可调整切片参数并重新切片

## 实施步骤

1. 修改数据库表结构
2. 创建 knowledge_base router
3. 创建 knowledge_base service
4. 创建前端 KnowledgeBase 组件
5. 修改 QuestionBook 添加入口
6. 测试完整流程