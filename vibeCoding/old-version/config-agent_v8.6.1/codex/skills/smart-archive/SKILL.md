---
name: smart-archive
description: 智能上下文归档
context: main
---
上下文 > 500K tokens 或手动触发时:
1. 已完成任务的详细日志 → `.ai_state/archive/`
2. 保留: session.md + doing.md + pitfalls.md + conventions.md
3. 归档: 已完成的 plan 条目、旧 review、旧 verified
4. 执行 `/compact` 压缩对话上下文
