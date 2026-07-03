---
name: lessons-loop
description: 自我改进循环 — 用户纠正后触发, 写入 knowledge.md 教训段
context: main
---
# 自我改进循环

## 触发条件
- 用户纠正了错误 (代码/设计/理解)
- 测试发现意外失败

## 执行
1. 识别: 什么错了 → 为什么错 → 什么条件下会重犯
2. 写入 `knowledge.md` 教训段:
   `## [日期] [模块] — [SCOPE/TECH/ARCH/IMPL/TEST/STYLE]`
   `- 错误/根因/规则`
3. 立即在当前任务应用新规则
4. 未来会话 R₀a 阶段回顾
