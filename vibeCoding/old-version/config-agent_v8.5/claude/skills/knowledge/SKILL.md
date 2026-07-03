---
name: knowledge
description: 跨会话经验管理 — 在 .ai_state 内沉淀和复用项目经验
context: main
---

# Knowledge

> 经验文件在 `.ai_state/` 内: patterns.md, pitfalls.md, decisions.md, tools.md。

## 写入格式

```markdown
## {日期} — {标题}
**场景**: {什么情况}
**教训**: {核心结论, 一句话}
```

## 写入时机

- E 阶段发现好模式 → patterns.md
- V 失败 / Rev 发现问题 → pitfalls.md
- D 阶段重大决策 → decisions.md
- 任意阶段工具心得 → tools.md

## 读取

SessionStart hook 自动加载 pitfalls.md。其他按需读取。
