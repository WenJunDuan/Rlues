---
name: phase-router
description: |
  Intent recognition and workflow routing. Analyzes user input to determine
  task type and routes to appropriate agent. Core decision layer.
---

# Phase Router Skill

## Routing Rules

| Input Pattern | Route To | Workflow |
|:---|:---|:---|
| No task ID + new keywords | requirement-mgr | 需求创建 |
| Task ID + change keywords | requirement-mgr | 变更管理 |
| Task ID + design keywords | design-mgr | 方案设计 |
| Task ID + develop keywords | impl-executor | 开发实施 |
| Task ID only | Query status | 智能推断 |

## Complexity Assessment (P.A.C.E.)

| Path | Criteria | Workflow | Duration |
|:---|:---|:---|:---|
| A | 单文件, <30行 | R1→E→R2 | 30-60分 |
| B | 2-10文件 | R1→I→P→E→R2 | 2-8小时 |
| C | >10文件, 跨模块 | 完整九步 | 数天+ |

## Output Format

```yaml
RouteDecision:
  intent: [new|change|design|develop|complete]
  task_id: REQ-xxx
  complexity: [A|B|C]
  agent: [requirement-mgr|design-mgr|impl-executor]
  workflow: [path-a|path-b|path-c]
```
