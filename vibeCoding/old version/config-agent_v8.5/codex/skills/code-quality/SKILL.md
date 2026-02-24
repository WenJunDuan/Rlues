---
name: code-quality
description: Rev 阶段 Plugin 编排顺序
context: main
---

# Code Quality

## Plugin 执行顺序 (Rev 阶段)

1. `code-review` → 6 个 sub-agent 并行审查
2. `security-guidance` → 安全扫描 (Path C+)
3. `pr-review-toolkit` → PR 规范 (有 PR 时)

Plugin 不可用 → 手动审查 + `npm audit`。

## 经验沉淀

发现的问题 → `pitfalls.md`, 好模式 → `patterns.md`, 工具心得 → `tools.md`。
