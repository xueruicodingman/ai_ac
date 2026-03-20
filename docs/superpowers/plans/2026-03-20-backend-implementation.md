# AC测评工具后端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建AC测评工具后端服务，使用LangChain实现AI工作流，提供胜任力模型、评估矩阵、题本生成、报告生成等API

**Architecture:** 
- FastAPI + Python后端服务
- SQLite数据库存储用户数据
- LangChain实现AI生成工作流
- API直连模式（用户提供API Key）
- 每个用户数据只保留最新一份（覆盖策略）

**Tech Stack:** Python 3.11+, FastAPI, LangChain, SQLite, python-docx, matplotlib

---

## File Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI应用入口
│   ├── config.py                  # 配置管理
│   ├── database.py                # 数据库连接与初始化
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── competency_model.py
│   │   ├── evaluation_matrix.py
│   │   ├── questionnaire.py
│   │   ├── assessment_record.py
│   │   ├── judge_handbook.py
│   │   ├── report.py
│   │   └── file.py
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── competency.py
│   │   ├── matrix.py
│   │   ├── questionnaire.py
│   │   ├── record.py
│   │   ├── handbook.py
│   │   └── report.py
│   ├── routers/                   # API路由
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── competency.py
│   │   ├── matrix.py
│   │   ├── questionnaire.py
│   │   ├── record.py
│   │   ├── handbook.py
│   │   ├── report.py
│   │   └── file.py
│   ├── services/                  # 业务逻辑
│   │   ├── __init__.py
│   │   ├── ai_service.py         # AI服务基类
│   │   ├── competency_service.py  # 胜任力模型生成
│   │   ├── matrix_service.py      # 评估矩阵生成
│   │   ├── questionnaire_service.py # 题本生成
│   │   ├── handbook_service.py    # 评委手册生成
│   │   └── report_service.py      # 报告生成
│   ├── workflows/                 # LangChain工作流
│   │   ├── __init__.py
│   │   ├── competency_workflow.py
│   │   ├── matrix_workflow.py
│   │   ├── beh_workflow.py
│   │   ├── lgd_workflow.py
│   │   ├── roleplay_workflow.py
│   │   ├── case_workflow.py
│   │   ├── vision_workflow.py
│   │   └── report_workflow.py
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── security.py           # JWT、密码加密
│       ├── document.py           # Word/PDF生成
│       └── parser.py             # Excel解析
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_competency.py
│   ├── test_matrix.py
│   ├── test_questionnaire.py
│   └── test_report.py
├── requirements.txt
└── README.md
```

---

## Database Schema

```sql
-- 用户表
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 胜任力模型表
CREATE TABLE competency_models (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  dimensions TEXT NOT NULL,
  source_files TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 评估矩阵表
CREATE TABLE evaluation_matrices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER UNIQUE NOT NULL,
  model_id INTEGER NOT NULL,
  tools TEXT NOT NULL,
  matrix TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (model_id) REFERENCES competency_models(id)
);

-- 测评记录表
CREATE TABLE assessment_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER UNIQUE NOT NULL,
  model_id INTEGER,
  matrix_id INTEGER,
  upload_file_id INTEGER,
  score_table TEXT NOT NULL,
  behavior_table TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 题本表（每种工具一条）
CREATE TABLE questionnaires (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  tool_id VARCHAR(50) NOT NULL,
  model_id INTEGER NOT NULL,
  matrix_id INTEGER NOT NULL,
  content TEXT NOT NULL,
  word_url VARCHAR(500),
  pdf_url VARCHAR(500),
  status VARCHAR(20) DEFAULT 'completed',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE(user_id, tool_id)
);

-- 评委手册表
CREATE TABLE judge_handbooks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER UNIQUE NOT NULL,
  model_id INTEGER NOT NULL,
  matrix_id INTEGER NOT NULL,
  questionnaires TEXT NOT NULL,
  content TEXT NOT NULL,
  word_url VARCHAR(500),
  pdf_url VARCHAR(500),
  status VARCHAR(20) DEFAULT 'completed',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 报告表
CREATE TABLE reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  record_id INTEGER NOT NULL,
  report_type VARCHAR(50) NOT NULL,
  candidate_id VARCHAR(50) NOT NULL,
  candidate_name VARCHAR(100),
  scores_data TEXT,
  radar_chart_url VARCHAR(500),
  total_score DECIMAL(5,2),
  content TEXT NOT NULL,
  language VARCHAR(20) DEFAULT 'zh',
  word_url VARCHAR(500),
  pdf_url VARCHAR(500),
  status VARCHAR(20) DEFAULT 'draft',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (record_id) REFERENCES assessment_records(id),
  UNIQUE(user_id, report_type, candidate_id)
);

-- 文件表
CREATE TABLE files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  size INTEGER,
  file_path VARCHAR(500) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 用户设置表
CREATE TABLE user_settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER UNIQUE NOT NULL,
  api_key VARCHAR(500),
  default_model VARCHAR(50) DEFAULT 'gpt-4',
  theme VARCHAR(20) DEFAULT 'light',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## Task 1: 项目初始化

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/src/__init__.py`
- Create: `backend/src/config.py`
- Create: `backend/src/database.py`

- [ ] **Step 1: Create requirements.txt**

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.12
pydantic==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
sqlalchemy==2.0.35
aiosqlite==0.20.0
langchain==0.3.7
langchain-openai==0.2.6
langchain-core==0.3.18
langchain-community==0.3.5
openai==1.54.4
python-docx==1.1.2
reportlab==4.2.5
matplotlib==3.9.2
openpyxl==3.1.5
pandas==2.2.3
```

- [ ] **Step 2: Create config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "AC测评工具"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./ac_assessment.db"
    
    UPLOAD_DIR: str = "./uploads"
    GENERATED_DIR: str = "./generated"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

- [ ] **Step 3: Create database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session_maker() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 4: Commit**

```bash
cd /Users/ximenruixue/Desktop/AC_AI && git add backend/ && git commit -m "feat: initialize backend project structure"
```

---

## Task 2: 用户认证模块

**Files:**
- Create: `backend/src/models/user.py`
- Create: `backend/src/schemas/auth.py`
- Create: `backend/src/routers/auth.py`
- Create: `backend/src/utils/security.py`
- Modify: `backend/src/main.py`

- [ ] **Step 1: Create user model**

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from src.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Create auth schemas**

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: int | None = None
```

- [ ] **Step 3: Create security utils**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        return user_id
    except JWTError:
        return None
```

- [ ] **Step 4: Create auth router**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.user import User
from src.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from src.utils.security import get_password_hash, verify_password, create_access_token, decode_token

router = APIRouter(prefix="/api/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user_id = decode_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证凭证")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="邮箱已注册")
    
    user = User(email=user_data.email, password_hash=get_password_hash(user_data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse(id=user.id, email=user.email, created_at=str(user.created_at))

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email, created_at=str(current_user.created_at))
```

- [ ] **Step 5: Update main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import init_db
from src.routers import auth

app = FastAPI(title="AC测评工具API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def root():
    return {"message": "AC测评工具API"}
```

- [ ] **Step 6: Test auth**

Run: `cd backend && uvicorn src.main:app --reload`
Expected: Server starts, endpoints respond

- [ ] **Step 7: Commit**

```bash
cd /Users/ximenruixue/Desktop/AC_AI && git add backend/ && git commit -m "feat: add user authentication module"
```

---

## Task 3: AI服务基类和胜任力模型工作流

**Files:**
- Create: `backend/src/services/ai_service.py`
- Create: `backend/src/workflows/competency_workflow.py`
- Create: `backend/src/services/competency_service.py`
- Create: `backend/src/schemas/competency.py`
- Create: `backend/src/routers/competency.py`

- [ ] **Step 1: Create AI service base class**

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

class AIService(ABC):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=0.7
        )
    
    @abstractmethod
    async def generate(self, **kwargs) -> Dict[str, Any]:
        pass
    
    def create_prompt(self, system: str, human: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system),
            HumanMessage(content=human)
        ])
    
    async def call_llm(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        chain = prompt | self.llm
        response = await chain.ainvoke(kwargs)
        return response.content
```

- [ ] **Step 2: Create competency workflow**

```python
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

COMPETENCY_SYSTEM_PROMPT = """你是一位资深的人才评估专家，擅长构建胜任力模型。
根据提供的背景材料和要求，生成专业的胜任力模型。
输出格式为JSON，包含以下字段：
- dimensions: 能力维度数组
  - name: 能力名称
  - meaning: 能力含义
  - behavior_criteria: 行为标准数组
    - title: 行为标准标题
    - description: 行为标准描述"""

COMPETENCY_HUMAN_PROMPT = """请根据以下信息生成胜任力模型：

背景材料：{background}
指定能力：{specified_abilities}
能力数量：{num_competencies}

请生成一个专业的胜任力模型，包含{dimensions_count}个能力维度。"""

class CompetencyWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        background: str = "",
        specified_abilities: List[str] = None,
        num_competencies: int = 5
    ) -> Dict[str, Any]:
        specified = ", ".join(specified_abilities) if specified_abilities else "无"
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=COMPETENCY_SYSTEM_PROMPT),
            HumanMessage(content=COMPETENCY_HUMAN_PROMPT.format(
                background=background or "无",
                specified_abilities=specified,
                num_competencies=num_competencies,
                dimensions_count=num_competencies
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        
        import json
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content)
        for dim in result.get("dimensions", []):
            import uuid
            dim["id"] = str(uuid.uuid4())
            for bc in dim.get("behavior_criteria", []):
                bc["id"] = str(uuid.uuid4())
        
        return result
```

- [ ] **Step 3: Create competency service**

```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.services.ai_service import AIService
from src.workflows.competency_workflow import CompetencyWorkflow

class CompetencyService(AIService):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        self.workflow = CompetencyWorkflow(self.llm)
    
    async def generate(
        self,
        background: str = "",
        specified_abilities: Optional[List[str]] = None,
        num_competencies: int = 5
    ) -> dict:
        return await self.workflow.generate(
            background=background,
            specified_abilities=specified_abilities,
            num_competencies=num_competencies
        )
```

- [ ] **Step 4: Create competency schemas**

```python
from pydantic import BaseModel
from typing import List, Optional

class BehaviorCriterion(BaseModel):
    id: str
    title: str
    description: str

class Dimension(BaseModel):
    id: str
    name: str
    meaning: str
    behavior_criteria: List[BehaviorCriterion]

class CompetencyModelCreate(BaseModel):
    name: str = "胜任力模型"
    dimensions: List[Dimension]
    source_files: Optional[List[str]] = None

class CompetencyModelResponse(BaseModel):
    id: int
    name: str
    dimensions: List[Dimension]
    source_files: Optional[List[str]] = None
    created_at: str
    updated_at: str

class CompetencyGenerateRequest(BaseModel):
    background: Optional[str] = None
    files: Optional[List[str]] = None
    specified_abilities: Optional[List[str]] = None
    num_competencies: int = 5
    api_key: str
```

- [ ] **Step 5: Create competency router**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.models.competency_model import CompetencyModel
from src.schemas.competency import (
    CompetencyModelCreate, CompetencyModelResponse, CompetencyGenerateRequest
)
from src.services.competency_service import CompetencyService
import json

router = APIRouter(prefix="/api/competency-models", tags=["胜任力模型"])

@router.post("/generate")
async def generate_competency_model(
    request: CompetencyGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    service = CompetencyService(api_key=request.api_key)
    result = await service.generate(
        background=request.background,
        specified_abilities=request.specified_abilities,
        num_competencies=request.num_competencies
    )
    return {"success": True, "data": result}

@router.get("", response_model=CompetencyModelResponse)
async def get_competency_model(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CompetencyModel).where(CompetencyModel.user_id == current_user.id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="未找到胜任力模型")
    
    return CompetencyModelResponse(
        id=model.id,
        name=model.name,
        dimensions=json.loads(model.dimensions),
        source_files=json.loads(model.source_files) if model.source_files else None,
        created_at=str(model.created_at),
        updated_at=str(model.updated_at)
    )

@router.post("", response_model=CompetencyModelResponse)
async def save_competency_model(
    data: CompetencyModelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CompetencyModel).where(CompetencyModel.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    model = existing or CompetencyModel(user_id=current_user.id)
    model.name = data.name
    model.dimensions = json.dumps([d.model_dump() for d in data.dimensions], ensure_ascii=False)
    model.source_files = json.dumps(data.source_files or [], ensure_ascii=False)
    
    if not existing:
        db.add(model)
    
    await db.commit()
    await db.refresh(model)
    
    return CompetencyModelResponse(
        id=model.id,
        name=model.name,
        dimensions=json.loads(model.dimensions),
        source_files=json.loads(model.source_files) if model.source_files else None,
        created_at=str(model.created_at),
        updated_at=str(model.updated_at)
    )
```

- [ ] **Step 6: Commit**

```bash
cd /Users/ximenruixue/Desktop/AC_AI && git add backend/ && git commit -m "feat: add competency model AI workflow"
```

---

## Task 4: 评估矩阵工作流

**Files:**
- Create: `backend/src/workflows/matrix_workflow.py`
- Create: `backend/src/services/matrix_service.py`
- Create: `backend/src/schemas/matrix.py`
- Create: `backend/src/routers/matrix.py`

- [ ] **Step 1: Create matrix workflow**

```python
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

MATRIX_SYSTEM_PROMPT = """你是一位人才评估专家，擅长设计评估矩阵。
根据胜任力模型和测评工具，生成最优的评估矩阵配对。
输出格式为JSON，包含matrix字段，格式为：{dimension_name: {tool_id: true/false}}"""

MATRIX_HUMAN_PROMPT = """胜任力模型：{competency_model}

测评工具：{tools}

请为每个能力维度选择最适合的测评工具，生成评估矩阵。
规则：
- 每个能力维度至少选择1-2个工具
- 选择最能评估该能力维度的工具组合
- 考虑工具之间的互补性"""

TOOLS = [
    {"id": "beh", "name": "BEI行为事件访谈"},
    {"id": "lgd", "name": "无领导小组讨论"},
    {"id": "roleplay", "name": "角色扮演"},
    {"id": "case", "name": "案例分析"},
    {"id": "vision", "name": "个人愿景"}
]

class MatrixWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        tools = tools or TOOLS
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=MATRIX_SYSTEM_PROMPT),
            HumanMessage(content=MATRIX_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                tools=str([t["name"] for t in tools])
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        
        import json
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content)
        return result
```

- [ ] **Step 2: Create matrix service and router** (similar pattern to competency)

- [ ] **Step 3: Commit**

---

## Task 5: 题本生成工作流（5种工具）

**Files:**
- Create: `backend/src/workflows/beh_workflow.py`
- Create: `backend/src/workflows/lgd_workflow.py`
- Create: `backend/src/workflows/roleplay_workflow.py`
- Create: `backend/src/workflows/case_workflow.py`
- Create: `backend/src/workflows/vision_workflow.py`
- Create: `backend/src/services/questionnaire_service.py`
- Create: `backend/src/schemas/questionnaire.py`
- Create: `backend/src/routers/questionnaire.py`

- [ ] **Step 1: Create BEI workflow**

```python
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

BEH_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长设计BEI行为事件访谈题本。
根据胜任力模型和评估矩阵，生成专业的BEI题本。
题本应包含：
1. 指导语
2. 开场提问
3. 每个能力维度的追问问题（使用STAR法则）
4. 结束语

输出格式为Markdown"""

BEI_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵（BEI相关部分）：
{matrix}

要求：
- 为每个能力维度设计3-5个行为事件访谈问题
- 问题应引导被测者描述具体事例
- 使用STAR法则（情境、任务、行动、结果）
- 语言专业、清晰"""

class BEHWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        extra_requirements: str = ""
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=BEH_SYSTEM_PROMPT),
            HumanMessage(content=BEI_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix.get("matrix", {}))
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
```

- [ ] **Step 2: Create other 4 workflows** (LGD, RolePlay, Case, Vision)

- [ ] **Step 3: Create questionnaire service and router**

- [ ] **Step 4: Commit**

---

## Task 6: 评委手册工作流

**Files:**
- Create: `backend/src/workflows/handbook_workflow.py`
- Create: `backend/src/services/handbook_service.py`
- Create: `backend/src/schemas/handbook.py`
- Create: `backend/src/routers/handbook.py`

- [ ] **Step 1: Create handbook workflow**

```python
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

HANDBOOK_SYSTEM_PROMPT = """你是一位资深人才评估专家，擅长编写评委手册。
根据已生成的5种测评题本，生成完整的评委手册。
手册应包含：
1. 测评说明（每个环节的目的、时长、评估重点）
2. 评分标准（每个能力维度的5级评分标准）
3. 注意事项（评委须知、行为记录要求等）
4. 行为记录表模板

输出格式为Markdown"""

HANDBOOK_HUMAN_PROMPT = """胜任力模型：
{competency_model}

评估矩阵：
{matrix}

题本内容：
{questionnaires}

请生成完整的评委手册"""

class HandbookWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate(
        self,
        competency_model: Dict[str, Any],
        evaluation_matrix: Dict[str, Any],
        questionnaires: List[Dict[str, str]]
    ) -> str:
        qa_content = "\n\n".join([
            f"【{q['tool_id']}】\n{q['content']}"
            for q in questionnaires
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=HANDBOOK_SYSTEM_PROMPT),
            HumanMessage(content=HANDBOOK_HUMAN_PROMPT.format(
                competency_model=str(competency_model.get("dimensions", [])),
                matrix=str(evaluation_matrix),
                questionnaires=qa_content
            ))
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
```

- [ ] **Step 2: Create handbook service and router**

- [ ] **Step 3: Commit**

---

## Task 7: 报告生成工作流（3种报告）

**Files:**
- Create: `backend/src/workflows/report_workflow.py`
- Create: `backend/src/services/report_service.py`
- Create: `backend/src/schemas/report.py`
- Create: `backend/src/routers/report.py`

- [ ] **Step 1: Create report workflow**

```python
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

FEEDBACK_REPORT_PROMPT = """你是一位资深人才评估专家，擅长撰写反馈版报告。
根据被测者的测评数据，生成专业的反馈报告。

报告结构：
1. 一句话评价
2. 优势项（能力名称、评价语、行为表现）
3. 不足项（能力名称、评价语、行为表现）

要求：
- 语言专业、客观
- 基于具体数据和行为
- 优势与不足都要有行为证据支持"""

class ReportWorkflow:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate_feedback_report(
        self,
        candidate: Dict[str, Any],
        competency_model: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=FEEDBACK_REPORT_PROMPT),
            HumanMessage(content=f"被测者：{candidate.get('name')}\n得分：{candidate.get('scores')}\n行为记录：{candidate.get('behaviors', {})}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        
        import json
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        return json.loads(content)
```

- [ ] **Step 2: Create report service and router**

- [ ] **Step 3: Commit**

---

## Task 8: 文件处理和文档生成

**Files:**
- Create: `backend/src/routers/file.py`
- Create: `backend/src/utils/document.py`
- Create: `backend/src/utils/parser.py`

- [ ] **Step 1: Create file router for upload/download**

- [ ] **Step 2: Create document generation utility**

```python
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import matplotlib.pyplot as plt
import io
import base64

def markdown_to_docx(content: str, title: str = "") -> bytes:
    doc = Document()
    if title:
        heading = doc.add_heading(title, 0)
        heading.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            doc.add_heading(line[2:], 1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], 2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], 3)
        elif line.strip():
            doc.add_paragraph(line)
    
    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()

def generate_radar_chart(scores: Dict[str, float], title: str = "能力雷达图") -> str:
    categories = list(scores.keys())
    values = list(scores.values())
    values += values[:1]
    
    angles = [n / float(len(categories)) * 2 * 3.14159 for n in range(len(categories))]
    angles += angles[:1]
    
    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title(title)
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()
```

- [ ] **Step 3: Create Excel parser utility**

- [ ] **Step 4: Commit**

---

## Task 9: 集成测试

- [ ] **Step 1: Test full flow**

```bash
# Start server
cd backend && uvicorn src.main:app --reload

# Test register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test generate competency
curl -X POST http://localhost:8000/api/competency-models/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"api_key":"sk-xxx","num_competencies":5}'
```

- [ ] **Step 2: Commit**

---

## Summary

**Backend Structure:**
- FastAPI + SQLAlchemy + SQLite
- LangChain for AI workflows
- 8 main tasks covering all AI generation features
- Each workflow returns data matching frontend display format
- Override storage strategy per requirements

**Frontend Integration Points:**
- `/api/auth/*` - Login/register
- `/api/competency-models/*` - Competency model CRUD + AI generate
- `/api/evaluation-matrices/*` - Matrix CRUD + AI generate
- `/api/questionnaires/*` - 5 questionnaire types
- `/api/judge-handbooks/*` - Judge handbook
- `/api/reports/*` - 3 report types
- `/api/files/*` - File upload/download
