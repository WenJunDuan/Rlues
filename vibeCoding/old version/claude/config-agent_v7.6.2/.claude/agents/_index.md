# AI 角色索引

## 概述
VibeCoding 定义了 5 个专业角色，用于多 AI 协作和任务分工。

## 角色清单

| 角色 | 文件 | 职责 |
|:---|:---|:---|
| Orchestrator | orchestrator.md | 任务调度、流程控制 |
| Architect | architect.md | 架构设计、技术决策 |
| Developer | developer.md | 代码实现、重构 |
| Reviewer | reviewer.md | 代码审查、质量保证 |
| Product | product.md | 需求分析、产品对齐 |

## 角色使用

### 自动选择
根据当前阶段自动匹配角色:
```yaml
Research: Product (需求理解)
Innovate: Architect (设计)
Plan: Orchestrator (规划)
Execute: Developer (实现)
Review: Reviewer (验证)
```

### 显式调用
```
/role architect  # 切换到架构师视角
/role developer  # 切换到开发者视角
```

## 角色协作
```
Product (需求) 
    ↓
Architect (设计)
    ↓
Orchestrator (规划)
    ↓
Developer (实现)
    ↓
Reviewer (验证)
```

## 与引擎的关系
```yaml
角色: 定义职责和行为规范
引擎: 提供执行能力

示例:
  - Developer 角色 + Claude 引擎 = 智能开发
  - Developer 角色 + Codex 引擎 = 快速代码生成
```
