---
name: vibe-resume
description: 中断恢复 — 读取 .ai_state/ 还原上次进度, 从断点继续
allowed-tools: Read, augment-context-engine
---

# /vibe-resume — 中断恢复

## 执行步骤

1. 读 `.ai_state/doing.md` → 获取上次进度
2. 读 `.ai_state/session.md` → 获取需求和 Path
3. 读 `.ai_state/design.md` (如有) → 获取设计决策
4. 读 `.ai_state/plan.md` (如有) → 获取任务列表
5. `augment-context-engine` 搜最近修改的文件 → 理解代码当前状态
6. 输出恢复摘要:
   ```
   恢复会话: {需求}
   Path: {路径}
   当前阶段: {从 doing.md 推断}
   已完成: {☑ 列表}
   待完成: {☐ 列表}
   → 从 {下一个 ☐ 任务} 继续
   ```
7. 自动进入对应 RIPER-7 阶段继续

## .ai_state 不存在

→ 提示用户先 `/vibe-init`, 或直接 `/vibe-dev` 开新任务。
