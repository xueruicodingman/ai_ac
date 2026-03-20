# AC测评工具后端

基于FastAPI的AC测评工具后端服务，提供胜任力模型、评估矩阵、题本生成、报告生成等AI能力。

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境

复制 `.env.example` 为 `.env` 并修改配置：

```
SECRET_KEY=your-secret-key
```

### 3. 启动服务

```bash
uvicorn src.main:app --reload
```

服务将在 http://localhost:8000 启动。

### 4. API文档

访问 http://localhost:8000/docs 查看Swagger API文档。

## API端点

### 认证
- POST /api/auth/register - 用户注册
- POST /api/auth/login - 用户登录
- GET /api/auth/me - 获取当前用户

### 胜任力模型
- POST /api/competency-models/generate - AI生成模型
- GET /api/competency-models - 获取已保存模型
- POST /api/competency-models - 保存模型

### 评估矩阵
- POST /api/evaluation-matrices/generate - AI生成矩阵
- GET /api/evaluation-matrices - 获取已保存矩阵
- POST /api/evaluation-matrices - 保存矩阵
- GET /api/evaluation-matrices/tools - 获取工具列表

### 题本生成
- POST /api/questionnaires/generate - AI生成题本
- GET /api/questionnaires - 获取用户所有题本
- GET /api/questionnaires/{tool_id} - 获取指定题本
- POST /api/questionnaires - 保存题本
- GET /api/questionnaires/tools - 获取工具列表

### 评委手册
- POST /api/judge-handbooks/generate - AI生成手册
- GET /api/judge-handbooks - 获取已保存手册
- POST /api/judge-handbooks - 保存手册

### 报告生成
- POST /api/reports/generate/feedback - AI生成反馈版报告
- POST /api/reports/generate/org - AI生成组织版报告
- POST /api/reports/generate/personal - AI生成个人版报告
- GET /api/reports - 获取所有报告
- POST /api/reports - 保存报告

### 文件处理
- POST /api/files/upload - 上传文件
- POST /api/files/parse-assessment - 解析测评记录Excel
- GET /api/files/download-template - 下载模板
- GET /api/files/download/{file_id} - 下载文件
- POST /api/files/convert/markdown-to-docx - 转换为Word
- POST /api/files/generate-radar-chart - 生成雷达图

## 项目结构

```
backend/
├── src/
│   ├── main.py           # FastAPI应用入口
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库连接
│   ├── models/           # SQLAlchemy模型
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # API路由
│   ├── services/        # 业务逻辑
│   ├── workflows/       # LangChain工作流
│   └── utils/           # 工具函数
├── requirements.txt
└── README.md
```

## 使用说明

1. 注册并登录获取token
2. 在用户设置中配置API Key
3. 按流程：胜任力模型 → 评估矩阵 → 题本生成 → 评委手册
4. 上传测评记录
5. 生成反馈版 → 组织版 → 个人版报告
