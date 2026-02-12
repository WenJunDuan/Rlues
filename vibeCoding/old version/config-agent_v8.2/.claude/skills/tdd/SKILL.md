---
name: tdd
description: "Test-Driven Development with RED-GREEN-REFACTOR cycle and commit strategy per Path"
---

# TDD (RED-GREEN-REFACTOR)

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| Superpowers tdd | Plugin Skill | TDD 方法论 | 自动: E 阶段触发 |
| Superpowers subagent-driven-dev | Plugin Skill | 子任务并行 | 自动: 复杂任务时 |
| sou | MCP | 搜索现有测试风格 | `sou.search("相关测试")` |
| commit-commands | Plugin | 每次 GREEN 后提交 | 自动: `git commit` 时 |

## 铁律

代码在测试之前编写 → 删除代码，重写。无例外。

## 循环

```
RED:      写测试 → 运行 → 必须失败 (确认测试表达需求)
GREEN:    写最小代码 → 运行 → 必须通过
REFACTOR: 优化代码 → 运行 → 测试仍通过
```

## 执行方式

```
1. 从 todo.md 取 TDD 任务
2. sou.search("相关测试") → 了解项目测试风格
3. → Superpowers tdd: 执行 RED-GREEN-REFACTOR
   降级: SP 未安装 → 直接执行上述循环
4. 复杂任务 → Superpowers subagent-driven-dev:
   子任务 A: 写测试 (RED)
   子任务 B: 实现代码 (GREEN)
   降级: SP 未安装 → 顺序执行
5. 更新 doing.md → done.md
```

## 提交策略

| Path | 提交时机 | 说明 |
|:---|:---|:---|
| A | 改完直接 commit | 不走 TDD |
| B | 每个 TASK 完成后 | `feat: implement TASK-N` |
| C/D | 每个 GREEN 后 | 小步提交，便于 bisect |

提交由 commit-commands plugin 自动格式化 (Conventional Commits)。

## Plan 集成

P 阶段 todo.md 中，TDD 任务交替:

```
[TASK-1] 写 LoginForm 测试 (RED)        | 3min
[TASK-2] 实现 LoginForm (GREEN)          | 5min
[TASK-3] 重构 LoginForm (REFACTOR)       | 3min
```

## 强制级别

| Path | TDD | 覆盖率 |
|:---|:---|:---|
| A | 跳过 | — |
| B | 推荐 (--no-tdd 跳) | 60% |
| C | 强制 | 80% |
| D | 强制 (每个 teammate) | 85% |
