# /vibe-dev

## 用途
需求研发主入口，通过 phase-router 智能路由到相应流程。

## 语法
```bash
/vibe-dev <任务描述|任务ID> [选项]
```

## 参数
| 参数 | 说明 | 示例 |
|:---|:---|:---|
| 任务描述 | 新建任务的描述 | "添加用户登录" |
| 任务ID | 继续已有任务 | REQ-001 |

## 选项
| 选项 | 说明 |
|:---|:---|
| `--path=A\|B\|C` | 强制指定路径 |
| `--design` | 进入设计阶段 |
| `--develop` | 进入开发阶段 |
| `--plan-only` | 仅生成计划 |
| `--design-only` | 仅设计不开发 |
| `--init` | 初始化项目 |

## 执行流程

### 1. 意图识别
```yaml
Agent: phase-router

分析:
  - 提取任务ID
  - 识别关键词
  - 评估复杂度
  - 确定路由目标
```

### 2. 智能路由
```yaml
无任务ID + 新建意图:
  → requirement-mgr → 需求创建

有任务ID + 设计意图:
  → design-mgr → 方案设计

有任务ID + 开发意图:
  → impl-executor → 开发实施

仅任务ID:
  → 查询状态 → 继续当前阶段
```

### 3. 执行流程
```yaml
根据路由结果:
  - 加载对应 Agent
  - 触发相关 Skills
  - 自动检索知识库
  - 自动检索经验库
  - 执行九步工作流
```

## 使用示例

### 新建需求
```bash
/vibe-dev "添加用户登录功能"

# 执行:
# 1. phase-router: 识别为新建需求
# 2. knowledge-base: 检索项目背景
# 3. experience: 检索类似需求经验
# 4. requirement-mgr: 创建需求文档
# 5. [REQ_READY] 寸止等待确认
```

### 继续任务
```bash
/vibe-dev REQ-001

# 执行:
# 1. phase-router: 识别任务ID
# 2. 查询任务状态: 需求已确认，待设计
# 3. 路由到: design-mgr
# 4. 继续方案设计流程
```

### 指定动作
```bash
/vibe-dev REQ-001 --develop

# 强制进入开发阶段
```

### 快速修复
```bash
/vibe-dev --path=A "修复按钮样式"

# 使用 Path A 快速流程
```

## 状态文件
```yaml
创建/更新:
  - .ai_state/requirements/REQ-xxx.md (需求)
  - .ai_state/designs/DESIGN-xxx.md (设计)
  - .ai_state/meta/kanban.md (状态)
  - .ai_state/meta/session.lock (会话)
```

## 与知识库/经验的集成
```yaml
自动触发:
  - 需求阶段: 检索项目背景、类似需求经验
  - 设计阶段: 检索架构规范、技术决策经验
  - 开发阶段: 检索代码规范、编码经验
  - 完成阶段: 沉淀新经验
```
