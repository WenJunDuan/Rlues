---
name: vibe-resume
description: 从中断处恢复开发
---
## 执行步骤
1. 读 .ai_state/session.md → 恢复: 当前阶段 + Path + 需求摘要
2. 读 .ai_state/doing.md → 进行中任务 (如有)
3. 读 .ai_state/plan.md → 完成/未完成 (如有)
4. 告知用户: "上次中断在 {阶段}, 正在处理: {描述}。继续?"
5. 用户确认后, 从断点阶段继续执行 riper-7.md
