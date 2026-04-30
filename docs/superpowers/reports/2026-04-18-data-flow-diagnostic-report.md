# 数据流转诊断报告

**生成时间**: 2026-04-18  
**诊断范围**: 胜任力模型 → 评估矩阵 → 题本生成 → 评委手册生成 → 模拟练习 → 行为评价 → 测评报告

---

## 一、数据流转总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据流转图                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  胜任力模型   │───▶│  评估矩阵    │───▶│  题本生成    │───▶│ 评委手册  │ │
│  │CompetencyModel│    │EvaluationMatrix│  │Questionnaire │   │JudgeHandbook│ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘ │
│         │                    │                    │                   │       │
│         ▼                    ▼                    ▼                   ▼       │
│  {id, name,         {id, model_id,     {id, tool_id,     {tool,         │       │
│   dimensions[],      tools[],          model_id,        judge_content,│       │
│   source_files[]    matrix:{}}         matrix_id,       actor_content │       │
│                                       content,                       │       │
│                                       status}                         │       │
│                                                                             │
│                                           │                             │       │
│                                           ▼                             │       │
│                              ┌────────────────────────────┐             │       │
│                              │       模拟练习             │             │       │
│                              │   RolePlayPracticeService   │◀───────────┘       │
│                              └────────────────────────────┘                  │
│                                         │                             │
│                                         ▼                             │
│                              ┌────────────────────────────┐             │
│                              │      行为评价/测评报告        │             │
│                              └────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、各模块数据格式规范

### 2.1 胜任力模型 (CompetencyModel)

| 字段 | 类型 | 说明 | 必需 |
|-----|------|------|-----|
| id | int | 主键 | 是 |
| name | string | 模型名称 | 是 |
| dimensions | Array | 能力维度列表 | 是 |
| dimensions[].id | string | 维度ID | 是 |
| dimensions[].name | string | 维度名称(如"学习能力") | 是 |
| dimensions[].meaning | string | 能力定义 | 是 |
| dimensions[].behavior_criteria | Array | 行为标准列表 | 是 |
| dimensions[].behavior_criteria[].id | string | 标准ID | 是 |
| dimensions[].behavior_criteria[].title | string | 标准标题 | 是 |
| dimensions[].behavior_criteria[].description | string | 标准描述 | 是 |
| source_files | Array | 源文件列表 | 否 |
| created_at | string | 创建时间 | 是 |
| updated_at | string | 更新时间 | 是 |

**API端点**:
- `GET /api/competency-models` - 获取模型
- `POST /api/competency-models` - 保存模型
- `POST /api/competency-models/generate` - 生成模型

---

### 2.2 评估矩阵 (EvaluationMatrix)

| 字段 | 类型 | 说明 | 必需 |
|-----|------|------|-----|
| id | int | 主键 | 是 |
| model_id | int | 关联的模型ID | 是 |
| tools | Array | 工具列表 | 是 |
| tools[].id | string | 工具ID(如"beh","lgd") | 是 |
| tools[].name | string | 工具名称 | 是 |
| tools[].weight | int | 权重(默认20) | 是 |
| tools[].enabled | bool | 是否启用 | 是 |
| matrix | Object | 评估矩阵 | 是 |
| matrix[能力名] | Object | 能力维度 | 是 |
| matrix[能力名][工具ID] | bool | 该工具是否考察该能力 | 是 |

**示例**:
```json
{
  "matrix": {
    "学习能力": {"beh": true, "lgd": false},
    "团队管理": {"beh": true, "roleplay": true},
    "沟通协作": {"beh": true, "lgd": true, "roleplay": true},
    "解决问题": {"case": true, "vision": true, "lgd": true}
  }
}
```

**API端点**:
- `GET /api/evaluation-matrices` - 获取矩阵
- `POST /api/evaluation-matrices` - 保存矩阵
- `POST /api/evaluation-matrices/generate` - 生成矩阵

---

### 2.3 题本生成 (Questionnaire)

| 字段 | 类型 | 说明 | 必需 |
|-----|------|------|-----|
| id | int | 主键 | 是 |
| tool_id | string | 工具ID | 是 |
| model_id | int | 关联的模型ID | 是 |
| matrix_id | int | 关联的矩阵ID | 是 |
| content | string | 题本内容(Markdown格式) | 是 |
| word_url | string | Word文档URL | 否 |
| pdf_url | string | PDF文档URL | 否 |
| status | string | 状态 | 是 |

**API端点**:
- `GET /api/questionnaires` - 获取所有题本
- `GET /api/questionnaires/{tool_id}` - 获取指定题本
- `POST /api/questionnaires` - 保存题本
- `POST /api/questionnaires/generate` - 生成题本

---

### 2.4 评委手册 (JudgeHandbook)

| 字段 | 类型 | 说明 | 必需 |
|-----|------|------|-----|
| id | int | 主键 | 是 |
| tool | string | 工具ID | 是 |
| model_id | int | 关联的模型ID | 是 |
| matrix_id | int | 关联的矩阵ID | 是 |
| judge_content | string | 评委手册内容 | 是 |
| actor_content | string | 演员手册内容 | 否 |
| status | string | 状态 | 是 |

**API端点**:
- `GET /api/judge-handbooks` - 获取所有手册
- `GET /api/judge-handbooks/tool/{tool}` - 获取指定手册
- `POST /api/judge-handbooks` - 保存手册
- `POST /api/judge-handbooks/generate` - 生成手册

---

## 三、问题诊断

### 问题1: 评委手册生成API数据格式不匹配 ⚠️ HIGH

**症状**: `POST /api/judge-handbooks/generate` 返回 422 Unprocessable Entity

**根本原因**: 数据结构嵌套错误

**详细分析**:

后端期望的数据格式:
```python
{
    "competency_model": dict,       # 如 {"dimensions": [...], "name": "胜任力模型"}
    "evaluation_matrix": dict,   # 如 {"学习能力": {"beh": True}}
    "questionnaires": List[dict]  # 如 [{"tool_id": "beh", "content": "..."}]
}
```

前端实际发送的数据结构:
```javascript
{
    competency_model: {
        competency_model: {...},    // ❌ 嵌套了一层
        evaluation_matrix: {...},
        questionnaires: [...]
    },
    evaluation_matrix: undefined,  // ❌ 被嵌套后丢失
    questionnaires: []           // ❌ 被嵌套后丢失
}
```

**原因链**:
1. `getEvaluationMatrix()` 返回完整的 `MatrixResponse` 对象 (`{id, model_id, tools, matrix, created_at, updated_at}`)
2. 前端没有正确提取 `matrix` 字段
3. `generateJudgeHandbook()` 调用时传入了完整对象而非只传 `matrix`

---

### 问题2: 评估矩阵保存时未返回matrix字段 ⚠️ MEDIUM

**症状**: `GET /api/evaluation-matrices` 返回的数据没有`matrix`字段无法直接用于后续API

**详细分析**:

后端 `matrix.py` 的 `save_matrix` 返回 `MatrixResponse`:
```python
return MatrixResponse(
    id=matrix.id,
    model_id=matrix.model_id,
    tools=[Tool(**t) for t in json.loads(matrix.tools)],
    matrix=json.loads(matrix.matrix),  # ✅ 包含matrix
    ...
)
```

前端 `getEvaluationMatrix()`:
```javascript
const response = await fetch(`${API_BASE_URL}/api/evaluation-matrices`, {...});
return response.json();  // 返回 {id, model_id, tools, matrix, ...}
```

**状态**: 此功能正常，问题在于前端调用时未正确提取

---

### 问题3: 题本生成API的competency_model参数 ⚠️ MEDIUM

**症状**: 题本生成需要传递competency_model和evaluation_matrix

**后端 `questionnaire.py`**:
```python
async def generate_questionnaire(
    tool_id: str,
    competency_model: dict = Body(...),
    evaluation_matrix: dict = Body(...),
    ...
)
```

**需要的格式**:
- `competency_model`: `{"dimensions": [...]}`
- `evaluation_matrix`: `{"学习能力": {"beh": true, ...}}`

---

## 四、数据流转验证矩阵

| 源模块 | 目标模块 | 传递方式 | 状态 | 问题 |
|-------|---------|---------|------|------|
| 胜任力模型 | 评估矩阵 | 手动选择dimensions | ✅ 正常 | 无 |
| 评估矩阵 | 题本生成 | 直接使用matrix | ⚠️ 需要修复 | 见问题1 |
| 题本 | 角色扮演 | questionnaire_content | ✅ 正常 | 无 |
| 角色扮演 | 行为评价 | 交互历史 | ✅ 正常 | 无 |

---

## 五、解决方案

### 方案A: 修复评委手册API数据格式 (推荐)

**修改文件**: `frontend/src/app/components/JudgeManual.tsx`

**修改内容**: 正确提取数据字段

```typescript
// 修改前 (有问题)
const response = await generateJudgeHandbook({
  competency_model: model,           // ❌ 传入完整对象
  evaluation_matrix: matrix?.matrix || {},
  questionnaires: questionnaireList
});

// 修改后
const competencyModelData = {
  dimensions: model.dimensions || [],
  name: model.name || ''
};

const response = await generateJudgeHandbook({
  competency_model: competencyModelData,
  evaluation_matrix: matrix?.matrix || {},
  questionnaires: questionnaireList
});
```

### 方案B: 创建统一的数据提取Hook

**修改文件**: `frontend/src/app/api.ts`

添加数据格式化函数:

```typescript
export const formatCompetencyModel = (model: any) => ({
  dimensions: model.dimensions || [],
  name: model.name || ''
});

export const formatEvaluationMatrix = (matrix: any) => {
  // 处理可能的嵌套结构
  if (matrix?.matrix) return matrix.matrix;
  return matrix || {};
};
```

### 方案C: 后端API兼容处理

**修改文件**: `backend/src/routers/handbook.py`

添加数据提取逻辑:

```python
@router.post("/generate")
async def generate_handbook(
    request_data: dict = Body(...),
    ...
):
    # 处理可能的嵌套结构
    competency_model = request_data.get("competency_model")
    evaluation_matrix = request_data.get("evaluation_matrix")
    questionnaires = request_data.get("questionnaires", [])
    
    # 如果competency_model是嵌套的，提出来
    if isinstance(competency_model, dict) and "competency_model" in competency_model:
        competency_model = competency_model.get("competency_model")
    
    # 同样处理evaluation_matrix和questionnaires
    ...
```

---

## 六、测试建议

### 测试用例

1. **完整流程测试**
   - 生成胜任力模型 → 保存 → 获取
   - 生成评估矩阵 → 保存 → 获取
   - 生成题本(单工具) → 保存 → 获取
   - 生成评委手册 → 保存 → 获取

2. **数据格式测试**
   - 验证每个API返回的数据格式正确
   - 验证前端传递到下一个API的数据格式正确

3. **边界情况测试**
   - 空数据
   - 缺失字段
   - 格式错误

---

## 七、结论

### 需要修复的问题

| 优先级 | 问题 | 修复方案 |
|--------|------|----------|
| **HIGH** | 评委手册生成API数据格式不匹配 | 方案A或方案C |
| MEDIUM | 前端数据提取不统一 | 方案B |

### 建议的修复顺序

1. 首先修复评委手册生成API (问题1)
2. 然后创建统一的数据格式化函数 (方案B)
3. 最后进行全面测试验证

---

**报告完成**