# Agent 索引 (功能导向)

## 概述
VibeCoding v7.7 采用功能导向的 Agent 设计，每个 Agent 负责特定的功能领域。

## Agent 清单

| Agent | 文件 | 职责 |
|:---|:---|:---|
| Phase Router | phase-router.md | 意图识别与智能路由 |
| Requirement Manager | requirement-mgr.md | 需求全生命周期管理 |
| Design Manager | design-mgr.md | 方案全生命周期管理 |
| Implementation Executor | impl-executor.md | 开发实施执行 |
| Experience Manager | experience-mgr.md | 经验沉淀与管理 |

## 协作关系
```
用户输入
    ↓
┌─────────────────┐
│  Phase Router   │ ← 意图识别与路由
└────────┬────────┘
         │
    ┌────┴────┬────────────┬────────────┐
    ↓         ↓            ↓            ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Req Mgr │ │Des Mgr │ │Impl Ex │ │Exp Mgr │
└────────┘ └────────┘ └────────┘ └────────┘
    需求       方案       开发       经验
```

## 路由规则

| 意图 | 目标 Agent | 触发 Skill |
|:---|:---|:---|
| 新建需求 | requirement-mgr | riper/research |
| 变更需求 | requirement-mgr | riper/research |
| 方案设计 | design-mgr | riper/innovate |
| 开发实施 | impl-executor | riper/execute |
| 经验检索 | experience-mgr | experience |
| 经验沉淀 | experience-mgr | experience |

## 与 v7.6 的区别

### v7.6 (角色导向)
```
orchestrator - 调度器
architect    - 架构师
developer    - 开发者
reviewer     - 审核者
product      - 产品
```

### v7.7 (功能导向)
```
phase-router    - 负责路由决策
requirement-mgr - 负责需求管理
design-mgr      - 负责方案管理
impl-executor   - 负责开发执行
experience-mgr  - 负责经验沉淀
```

## 优势
1. **职责清晰** - 每个 Agent 有明确的功能边界
2. **易于扩展** - 新增功能只需添加新 Agent
3. **便于路由** - 根据意图直接定位 Agent
4. **减少冲突** - 避免角色职责重叠
