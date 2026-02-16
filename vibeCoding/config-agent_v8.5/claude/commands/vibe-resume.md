---
name: vibe-resume
description: 中断恢复 — 从 .ai_state 断点继续
allowed-tools: Read, augment-context-engine
---

# /vibe-resume

1. 读 doing.md → session.md → pitfalls.md
2. `augment-context-engine` 搜最近修改文件
3. 输出: 需求、Path、已完成/待完成、下一步
4. 进入对应 RIPER-7 阶段继续

.ai_state 不存在 → 提示 /vibe-init 或 /vibe-dev。
