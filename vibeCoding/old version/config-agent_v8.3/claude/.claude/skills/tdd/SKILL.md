---
name: tdd
description: E 阶段 TDD 分级参数 — Path 决定强制级别和提交策略
context: main
---

# TDD — Path 分级参数

## SP tdd 自动处理 RED-GREEN-REFACTOR。本 skill 只添加:

### 分级策略

| Path | TDD 级别 | 提交策略 |
|:---|:---|:---|
| A | 跳过 | 直接 commit |
| B | 推荐 (核心逻辑) | 功能完成后 commit |
| C | 强制 (全覆盖) | RED/GREEN 交替 commit |
| D | 强制 + 集成测试 | 原子 commit + PR |

### Plan 集成

E 阶段每个任务循环:
1. 读 `doing.md` 当前任务
2. 写失败测试 (RED)
3. 写最小实现 (GREEN)
4. 重构 (REFACTOR, 可选)
5. `commit-commands` plugin 格式化 commit
6. 更新 `doing.md` ☑
7. 下一个任务

### context7 集成

需要库 API 文档时: `npx ctx7 resolve <library>` 拉取最新文档到 context。
不预加载, 按需拉取。
