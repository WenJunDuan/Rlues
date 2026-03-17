---
name: kaizen
description: 持续改进 — 交付后复盘 (NeoLabHQ kaizen 模式)
context: main
---
## 流程
1. 回顾: `git diff --stat` + `git log --oneline`
2. 三个必答问题:
   - 哪些决策正确? **为什么**? (记根因)
   - 哪里浪费时间? 根因? (工具不熟/设计返工/需求不清)
   - 什么模式可以复用?
3. 写入:
   - **knowledge.md**: `[日期] 领域: 可复用模式`
   - **lessons.md**: `[日期] 领域: 陷阱 → 正确做法`
   - **conventions.md**: 新规范 (如有)
4. 归档 → archive.md

## 原则: 每条 ≤2 行, 只记有价值的, 不记 AI 已知常识
