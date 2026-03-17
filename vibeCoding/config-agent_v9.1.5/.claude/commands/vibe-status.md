---
name: vibe-status
description: 查看当前开发进度
---
## 执行步骤
1. 读 .ai_state/session.md → 当前阶段 + Path
2. 读 .ai_state/plan.md → 计算: 已完成/总数
3. 读 .ai_state/doing.md → 进行中任务
4. 输出看板:
   ```
   🔹 阶段: E (执行) | Path: B
   📋 进度: 3/7 tasks (42%)
   🔄 进行中: Task 4 — 实现用户认证接口
   ✅ 已完成: Task 1, 2, 3
   ⬜ 待做: Task 5, 6, 7
   ```
