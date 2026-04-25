# 评委组管理功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在首页题本生成后面添加评委组管理功能，用于配置每个测评工具的评委角色与任务

**Architecture:** 新建judge_teams表，在Dashboard添加入口，创建独立的评委组管理页面

**Tech Stack:** FastAPI + SQLAlchemy + React + LLM

---

## 文件结构

```
backend/
├── src/
│   ├── models/
│   │   └── judge_team.py              # 新建
│   ├── routers/
│   │   └── judge_team.py              # 新建
│   ├── services/
│   │   └── judge_team_service.py      # 新建
│   └── main.py                        # 修改：注册router
frontend/src/app/
│   ├── api.ts                         # 修改：添加评委组API
│   ├── components/
│   │   ├── Dashboard.tsx             # 修改：添加入口
│   │   └── JudgeTeam.tsx             # 新建
│   └── App.tsx                       # 修改：添加路由
```

---

## Task 1: 创建数据库模型

**Files:**
- Create: `backend/src/models/judge_team.py`
- Test: `python -c "from src.models.judge_team import JudgeTeam; print('OK')"`

- [ ] **Step 1: 创建 judge_team.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from src.database import Base

class JudgeTeam(Base):
    __tablename__ = "judge_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tool = Column(String(20), nullable=False)  # beh/roleplay/lgd/case/vision
    judges = Column(JSON, nullable=False)  # [{"role": "主评委", "task": "..."}, ...]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: 创建数据库表**

```bash
cd /Users/ximenruixue/Desktop/AC_AI/backend
sqlite3 ac_assessment.db "CREATE TABLE IF NOT EXISTS judge_teams (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  tool VARCHAR(20) NOT NULL,
  judges TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);"
```

- [ ] **Step 3: 验证模型加载**

Run: `cd /Users/ximenruixue/Desktop/AC_AI/backend && python -c "from src.models.judge_team import JudgeTeam; print('OK')"`

---

## Task 2: 创建评委组 Service

**Files:**
- Create: `backend/src/services/judge_team_service.py`
- Test: `python -c "from src.services.judge_team_service import JudgeTeamService; print('OK')"`

- [ ] **Step 1: 创建 service**

```python
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.models.judge_team import JudgeTeam
from src.models.judge_handbook import JudgeHandbook
from src.config import settings

class JudgeTeamService:
    def __init__(self, db: AsyncSession, user_id: int, api_key: str = None, api_url: str = None):
        self.db = db
        self.user_id = user_id
        self.api_key = api_key or settings.API_KEY
        self.api_url = api_url or settings.API_URL
    
    async def get_judge_teams(self) -> Dict[str, Any]:
        """获取用户所有工具的评委组配置"""
        result = await self.db.execute(
            select(JudgeTeam).where(JudgeTeam.user_id == self.user_id)
        )
        teams = result.scalars().all()
        return {team.tool: json.loads(team.judges) for team in teams}
    
    async def get_judge_team(self, tool: str) -> Optional[List[Dict]]:
        """获取指定工具的评委组配置"""
        result = await self.db.execute(
            select(JudgeTeam).where(
                and_(JudgeHandbook.user_id == self.user_id, JudgeTeam.tool == tool)
            )
        )
        team = result.scalar_one_or_none()
        if team:
            return json.loads(team.judges)
        return None
    
    async def save_judge_team(self, tool: str, judges: List[Dict]) -> Dict:
        """保存评委组配置"""
        result = await self.db.execute(
            select(JudgeTeam).where(
                and_(JudgeTeam.user_id == self.user_id, JudgeTeam.tool == tool)
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.judges = json.dumps(judges)
        else:
            new_team = JudgeTeam(
                user_id=self.user_id,
                tool=tool,
                judges=json.dumps(judges)
            )
            self.db.add(new_team)
        
        await self.db.commit()
        return {"tool": tool, "judges": judges}
    
    async def generate_judges(self, tool: str) -> List[Dict]:
        """调用LLM生成评委角色与任务"""
        # 获取评委手册内容
        handbook_result = await self.db.execute(
            select(JudgeHandbook).where(
                and_(JudgeHandbook.user_id == self.user_id, JudgeHandbook.tool == tool)
            )
        )
        handbook = handbook_result.scalar_one_or_none()
        
        if not handbook or not handbook.judge_content:
            raise ValueError(f"未找到 tool={tool} 的评委手册，请先生成评委手册")
        
        # 调用LLM生成
        prompt = f"""你是一个AC测评的评委组设计专家。请根据以下评委手册，设计3个评委的角色与任务。

评委手册内容：
{handbook.judge_content[:3000]}

请为每个评委设计：
1. 角色名称（如：主评委、副评委、观察员）
2. 具体任务描述（该评委在测评中的职责）

输出JSON格式的数组，不要有其他内容：
[{{"role": "主评委", "task": "负责整体评估和决策"}}, {{"role": "副评委", "task": "辅助评估和记录"}}, {{"role": "观察员", "task": "关注行为细节和特殊情况"}}]"""
        
        import requests
        response = requests.post(
            f"{self.api_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": "default", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
            timeout=30
        )
        
        if response.status_code != 200:
            raise ValueError(f"LLM调用失败: {response.status_code}")
        
        content = response.json()["choices"][0]["message"]["content"]
        
        # 解析JSON
        try:
            # 尝试提取JSON数组
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                judges = json.loads(match.group())
            else:
                judges = json.loads(content)
            return judges
        except:
            raise ValueError("LLM返回内容解析失败")
```

- [ ] **Step 2: 验证导入**

Run: `cd /Users/ximenruixue/Desktop/AC_AI/backend && python -c "from src.services.judge_team_service import JudgeTeamService; print('OK')"`

---

## Task 3: 创建评委组 Router

**Files:**
- Create: `backend/src/routers/judge_team.py`
- Modify: `backend/src/main.py`

- [ ] **Step 1: 创建 router**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.services.judge_team_service import JudgeTeamService
from typing import List, Dict, Any
import json

router = APIRouter(prefix="/api/judge-teams", tags=["评委组管理"])

@router.get("")
async def get_all_judge_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户所有工具的评委组配置"""
    service = JudgeTeamService(db, current_user.id)
    return await service.get_judge_teams()

@router.get("/{tool}")
async def get_judge_team(
    tool: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定工具的评委组配置"""
    service = JudgeTeamService(db, current_user.id)
    judges = await service.get_judge_team(tool)
    if not judges:
        return {"tool": tool, "judges": []}
    return {"tool": tool, "judges": judges}

@router.post("/{tool}")
async def save_judge_team(
    tool: str,
    judges: List[Dict[str, str]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """保存评委组配置"""
    service = JudgeTeamService(db, current_user.id)
    result = await service.save_judge_team(tool, judges)
    return {"success": True, "data": result}

@router.post("/{tool}/generate")
async def generate_judges(
    tool: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """调用LLM生成评委角色与任务"""
    service = JudgeTeamService(db, current_user.id)
    try:
        judges = await service.generate_judges(tool)
        return {"success": True, "data": {"judges": judges}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 2: 注册router**

在 `backend/src/main.py` 添加：
```python
from src.routers.judge_team import router as judge_team_router
app.include_router(judge_team_router)
```

- [ ] **Step 3: 验证导入**

Run: `cd /Users/ximenruixue/Desktop/AC_AI/backend && python -c "from src.routers.judge_team import router; print('OK')"`

---

## Task 4: 前端 API

**Files:**
- Modify: `frontend/src/app/api.ts`

- [ ] **Step 1: 添加API**

```typescript
export const getJudgeTeams = async () => {
  const response = await fetch(`${API_BASE_URL}/api/judge-teams`, {
    headers: getHeaders()
  });
  if (!response.ok) throw new Error('获取评委组失败');
  return response.json();
};

export const getJudgeTeam = async (tool: string) => {
  const response = await fetch(`${API_BASE_URL}/api/judge-teams/${tool}`, {
    headers: getHeaders()
  });
  if (!response.ok) throw new Error('获取评委组失败');
  return response.json();
};

export const saveJudgeTeam = async (tool: string, judges: any[]) => {
  const response = await fetch(`${API_BASE_URL}/api/judge-teams/${tool}`, {
    method: 'POST',
    headers: { ...getHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(judges)
  });
  if (!response.ok) throw new Error('保存评委组失败');
  return response.json();
};

export const generateJudges = async (tool: string) => {
  const response = await fetch(`${API_BASE_URL}/api/judge-teams/${tool}/generate`, {
    method: 'POST',
    headers: getHeaders()
  });
  if (!response.ok) throw new Error('生成评委失败');
  return response.json();
};
```

---

## Task 5: Dashboard 添加入口

**Files:**
- Modify: `frontend/src/app/components/Dashboard.tsx`

- [ ] **Step 1: 添加入口**

在 modules 数组中题本生成后面添加：

```tsx
{
  icon: <Users size={24} />,  // 需要添加 Users import
  title: '评委组管理',
  description: '配置各工具评委的角色与任务',
  page: 'judge-team',
},
```

---

## Task 6: 创建评委组管理页面

**Files:**
- Create: `frontend/src/app/components/JudgeTeam.tsx`
- Modify: `frontend/src/app/App.tsx`

- [ ] **Step 1: 创建 JudgeTeam.tsx**

```tsx
import { useState, useEffect } from 'react';
import { ArrowLeft, RefreshCw, Save, Edit2, X } from 'lucide-react';
import { getJudgeTeam, saveJudgeTeam, generateJudges } from '../api';

interface JudgeTeamProps {
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

export default function JudgeTeam({ onBack, initialTool = 'roleplay' }: JudgeTeamProps) {
  const [selectedTool, setSelectedTool] = useState(initialTool);
  const [judges, setJudges] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ role: '', task: '' });

  useEffect(() => {
    loadJudgeTeam();
  }, [selectedTool]);

  const loadJudgeTeam = async () => {
    setLoading(true);
    try {
      const data = await getJudgeTeam(selectedTool);
      setJudges(data.judges || []);
    } catch (e) {
      setJudges([]);
    }
    setLoading(false);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const data = await generateJudges(selectedTool);
      setJudges(data.data.judges);
      alert('生成成功');
    } catch (err: any) {
      alert(err.message || '生成失败');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    try {
      await saveJudgeTeam(selectedTool, judges);
      alert('保存成功');
    } catch (err: any) {
      alert(err.message || '保存失败');
    }
  };

  const handleEdit = (index: number) => {
    setEditingIndex(index);
    setEditForm({ role: judges[index].role, task: judges[index].task });
  };

  const handleSaveEdit = () => {
    if (editingIndex !== null) {
      const newJudges = [...judges];
      newJudges[editingIndex] = { role: editForm.role, task: editForm.task };
      setJudges(newJudges);
      setEditingIndex(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-semibold">评委组管理</h1>
      </div>

      <div className="p-6 max-w-4xl mx-auto">
        {/* 工具选择 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">选择测评工具</label>
          <div className="flex gap-2 flex-wrap">
            {TOOLS.map(tool => (
              <button
                key={tool.id}
                onClick={() => setSelectedTool(tool.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
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

        {/* 操作按钮 */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-green-600 text-white rounded-lg flex items-center gap-2 hover:bg-green-700"
          >
            <RefreshCw size={16} className={generating ? 'animate-spin' : ''} />
            {generating ? '生成中...' : 'AI生成评委'}
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center gap-2 hover:bg-blue-700"
          >
            <Save size={16} />
            保存配置
          </button>
        </div>

        {/* 评委列表 */}
        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-medium text-gray-900 mb-4">评委配置 ({judges.length}/3)</h3>
          
          {loading ? (
            <div className="text-center py-8 text-gray-500">加载中...</div>
          ) : judges.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              暂无评委配置，点击"AI生成评委"自动生成
            </div>
          ) : (
            <div className="space-y-4">
              {judges.map((judge, index) => (
                <div key={index} className="border rounded-lg p-4">
                  {editingIndex === index ? (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">角色名称</label>
                        <input
                          type="text"
                          value={editForm.role}
                          onChange={e => setEditForm({...editForm, role: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">任务描述</label>
                        <textarea
                          value={editForm.task}
                          onChange={e => setEditForm({...editForm, task: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg min-h-[80px]"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveEdit}
                          className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm"
                        >
                          保存
                        </button>
                        <button
                          onClick={() => setEditingIndex(null)}
                          className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900">{judge.role}</span>
                        <button
                          onClick={() => handleEdit(index)}
                          className="text-blue-600 hover:text-blue-700 text-sm"
                        >
                          编辑
                        </button>
                      </div>
                      <p className="text-sm text-gray-600">{judge.task}</p>
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

- [ ] **Step 2: 修改 App.tsx**

添加导入和路由：
```tsx
import JudgeTeam from './components/JudgeTeam';

// 在 render 函数中添加
case 'judge-team':
  return <JudgeTeam onBack={goBack} />;
```

---

## Task 7: 测试

- [ ] **Step 1: 启动后端**

```bash
cd /Users/ximenruixue/Desktop/AC_AI/backend
source /opt/anaconda3/bin/activate root
export PYTHONPATH=/Users/ximenruixue/Desktop/AC_AI/backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: 测试API**

```bash
curl http://localhost:8000/api/judge-teams/roleplay
```

- [ ] **Step 3: 启动前端**

```bash
cd /Users/ximenruixue/Desktop/AC_AI/frontend
npm run dev
```

- [ ] **Step 4: 完整流程测试**
1. 进入首页，确认"评委组管理"入口存在
2. 点击进入评委组管理页面
3. 选择工具（如角色扮演）
4. 点击"AI生成评委"测试LLM生成
5. 编辑评委角色与任务
6. 保存配置

---

## 实施顺序

1. Task 1: 数据库模型
2. Task 2: Service
3. Task 3: Router
4. Task 4: 前端API
5. Task 5: Dashboard入口
6. Task 6: JudgeTeam页面
7. Task 7: 测试