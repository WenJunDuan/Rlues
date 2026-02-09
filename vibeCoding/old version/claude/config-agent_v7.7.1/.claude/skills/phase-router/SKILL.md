# Phase Router Skill

## 概述
意图识别与智能路由技能，根据用户输入自动识别意图并路由到相应的处理流程。

## 路由规则

### 基于任务ID的路由
```yaml
无任务ID:
  关键词: "新建/创建/添加/实现/开发"
  路由: → 需求创建流程
  Agent: requirement-mgr

有任务ID + 变更意图:
  关键词: "修改/变更/调整/更新"
  路由: → 变更管理流程
  Agent: requirement-mgr

有任务ID + 设计意图:
  关键词: "设计/架构/方案/规划"
  路由: → 方案设计流程
  Agent: design-mgr

有任务ID + 开发意图:
  关键词: "开发/实现/编码/实施"
  路由: → 开发实施流程
  Agent: impl-executor

有任务ID + 完成意图:
  关键词: "完成/发布/提交/归档"
  路由: → 流转归档流程
  Agent: impl-executor

仅任务ID:
  动作: 智能推断当前状态
  路由: → 继续当前阶段
```

### 基于复杂度的路由
```yaml
快速修复 (Path A):
  条件: 单文件 & <30行 & 无需设计
  流程: 简化九步 (需求→开发→提交)

计划开发 (Path B):
  条件: 2-10文件 & 需要简单设计
  流程: 标准九步

系统开发 (Path C):
  条件: >10文件 或 跨模块 或 新系统
  流程: 完整九步 + 分阶段迭代
```

## 意图识别

### 关键词匹配
```yaml
需求相关:
  - 新建, 创建, 添加, 新增
  - 功能, 需求, 特性, feature

变更相关:
  - 修改, 变更, 调整, 更新
  - 改, 换, 优化

设计相关:
  - 设计, 架构, 方案, 规划
  - 结构, 模块, 接口

开发相关:
  - 开发, 实现, 编码, 实施
  - 写, 做, 代码

完成相关:
  - 完成, 发布, 提交, 归档
  - 结束, 关闭, 上线
```

### 上下文推断
```yaml
若无明确关键词:
  1. 检查 .ai_state/meta/session.lock
  2. 读取当前任务状态
  3. 推断下一步操作

状态推断:
  需求已创建 & 未设计 → 方案设计
  方案已确认 & 未开发 → 开发实施
  开发已完成 & 未提交 → 代码提交
```

## 路由决策流程
```
用户输入
    ↓
┌─────────────────┐
│  提取任务ID     │ → 有ID? → 查询任务状态
└────────┬────────┘
         ↓ 无ID
┌─────────────────┐
│  关键词匹配     │ → 匹配成功? → 确定意图
└────────┬────────┘
         ↓ 无匹配
┌─────────────────┐
│  复杂度评估     │ → 选择路径 (A/B/C)
└────────┬────────┘
         ↓
┌─────────────────┐
│  路由到Agent    │ → 执行相应流程
└─────────────────┘
```

## Agent 路由表

| 意图 | Agent | 入口Skill |
|:---|:---|:---|
| 新建需求 | requirement-mgr | riper/research |
| 变更需求 | requirement-mgr | riper/research |
| 方案设计 | design-mgr | riper/innovate |
| 开发实施 | impl-executor | riper/execute |
| 经验沉淀 | experience-mgr | experience |
| 服务加载 | impl-executor | service-analysis |

## MCP 集成
```javascript
// 使用 sequential-thinking 进行复杂意图推断
sequential_thinking({
  problem: "判断用户意图",
  context: "用户输入: ..., 当前状态: ...",
  steps: [
    "提取关键词",
    "检查任务ID",
    "匹配意图模式",
    "确定路由目标"
  ]
})
```

## 使用示例

### 示例1: 新建需求
```
输入: "添加用户登录功能"
分析:
  - 任务ID: 无
  - 关键词: "添加" → 新建
  - 内容: "用户登录功能"
路由: → requirement-mgr → 需求创建
```

### 示例2: 继续开发
```
输入: "REQ-001 继续开发"
分析:
  - 任务ID: REQ-001
  - 关键词: "继续开发" → 开发意图
  - 状态查询: 方案已确认
路由: → impl-executor → 开发实施
```

### 示例3: 智能推断
```
输入: "REQ-001"
分析:
  - 任务ID: REQ-001
  - 关键词: 无
  - 状态查询: 需求已创建, 方案未设计
推断: 下一步应该是方案设计
路由: → design-mgr → 方案设计
```

## 输出格式
```yaml
路由决策:
  input: "用户原始输入"
  task_id: "REQ-xxx" | null
  intent: "create|change|design|develop|complete"
  complexity: "A|B|C"
  target_agent: "agent名称"
  target_skill: "skill路径"
  context:
    current_phase: "当前阶段"
    next_action: "下一步动作"
```

## 配置
```yaml
# orchestrator.yaml
phase_router:
  skill_path: skills/phase-router/SKILL.md
  default_path: B
  auto_infer: true
  keywords:
    create: [新建, 创建, 添加, 新增]
    change: [修改, 变更, 调整, 更新]
    design: [设计, 架构, 方案, 规划]
    develop: [开发, 实现, 编码, 实施]
    complete: [完成, 发布, 提交, 归档]
```
