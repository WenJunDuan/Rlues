---
name: tdd
---

# TDD (RED-GREEN-REFACTOR)

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| SP tdd | Superpowers | TDD 方法论 | 读取 ~/.codex/superpowers/skills/tdd/SKILL.md |
| SP subagent-driven-dev | Superpowers | 子任务并行 | 读取 ~/.codex/superpowers/skills/subagent-driven-dev/SKILL.md |
| sou | MCP | 搜索现有测试风格 | `sou.search("相关测试")` |

## 铁律

代码在测试之前编写 → 删除代码，重写。无例外。

## 循环

```
RED:      写测试 → 运行 → 必须失败
GREEN:    写最小代码 → 运行 → 必须通过
REFACTOR: 优化代码 → 运行 → 测试仍通过
```

## 执行方式

```
1. 从 todo.md 取 TDD 任务
2. sou.search("相关测试") → 了解项目测试风格
3. → SP tdd: 执行 RED-GREEN-REFACTOR
   降级: SP 未安装 → 直接执行上述循环
4. 复杂任务 → SP subagent-driven-dev
   降级: SP 未安装 → 顺序执行
5. 更新 doing.md → done.md
```

## 提交策略 (手动 Conventional Commits)

| Path | 提交时机 | 格式 |
|:---|:---|:---|
| A | 改完直接 commit | `fix: 描述` |
| B | 每个 TASK 完成后 | `feat: implement TASK-N` |
| C | 每个 GREEN 后 | `feat(module): TASK-N green` |

Codex 无 commit-commands plugin，手动写 Conventional Commits。

## 强制级别

| Path | TDD | 覆盖率 |
|:---|:---|:---|
| A | 跳过 | — |
| B | 推荐 (--no-tdd 跳) | 60% |
| C | 强制 | 80% |
