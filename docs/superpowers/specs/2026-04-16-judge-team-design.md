# 评委组管理功能设计

## 概述

在首页新增"评委组管理"功能，用于配置每个测评工具的评委角色与任务。评委角色与任务由LLM根据评委手册自动生成，用户可编辑和保存。

## 功能需求

1. **入口位置**：首页题本生成后面
2. **评委数量**：每个工具固定3个评委
3. **评委角色与任务**：由LLM根据评委手册生成
4. **用户操作**：可编辑、可采纳、可保存

## 数据库设计

### 新建 judge_teams 表

```python
class JudgeTeam(Base):
    __tablename__ = "judge_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tool = Column(String(20), nullable=False)  # beh/roleplay/lgd/case/vision
    judges = Column(JSON, nullable=False)  # 评委列表
    # judges 结构: [
    #   {"role": "主评委", "task": "负责整体评估和决策", "created_at": "..."},
    #   {"role": "副评委", "task": "辅助评估和记录", "created_at": "..."},
    #   {"role": "观察员", "task": "关注行为细节和特殊情况", "created_at": "..."}
    # ]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

## 后端设计

### Router 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/judge-teams` | GET | 获取用户所有工具的评委组配置 |
| `/api/judge-teams/{tool}` | GET | 获取指定工具的评委组配置 |
| `/api/judge-teams/{tool}` | POST | 保存评委组配置 |
| `/api/judge-teams/{tool}/generate` | POST | 调用LLM生成评委角色与任务 |

### LLM生成逻辑

**Prompt设计**：
```
你是一个AC测评的评委组设计专家。请根据以下评委手册和评价标准，设计3个评委的角色与任务。

评委手册内容：
{judge_handbook}

请为每个评委设计：
1. 角色名称（如：主评委、副评委、观察员）
2. 具体任务描述（该评委在测评中的职责）

输出JSON格式：
[
  {"role": "主评委", "task": "..."},
  {"role": "副评委", "task": "..."},
  {"role": "观察员", "task": "..."}
]
```

## 前端设计

### Dashboard 入口

在首页添加"评委组管理"卡片：
- 图标：Users 或 Shield 图标
- 标题：评委组管理
- 描述：配置各工具评委的角色与任务

### JudgeTeam 页面

1. **工具选择器**：切换 beh/roleplay/lgd/case/vision
2. **评委列表**：展示3个评委的角色与任务
3. **操作按钮**：
   - 生成：由LLM生成评委角色与任务
   - 编辑：修改角色名称和任务描述
   - 保存：将配置保存到数据库

### 页面流程

1. 用户选择工具
2. 如已有配置，显示已有评委信息
3. 用户可点击"生成"让LLM生成新配置
4. 生成后显示编辑界面，用户可修改
5. 点击"保存"保存到数据库

## 用户流程

1. 进入首页，点击"评委组管理"
2. 选择测评工具（如角色扮演）
3. 如需生成评委角色，点击"生成"按钮
4. LLM阅读该工具的评委手册，生成3个评委角色
5. 用户可编辑角色名称和任务描述
6. 点击"保存"完成配置

## 实施步骤

1. 创建数据库模型
2. 创建后端router和service
3. 在Dashboard添加入口
4. 创建前端JudgeTeam页面
5. 测试完整流程