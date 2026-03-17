---
name: vibe-dev
description: 开始开发 — P.A.C.E. 路由 + RIPER 执行
---
接收需求: $ARGUMENTS

## 执行
1. 如果 .ai_state/ 不存在, 先 /vibe-init
2. 读 .claude/workflows/pace.md → 评估复杂度 → 选择 Path
3. 读 .claude/workflows/riper-7.md → 按所选 Path 逐阶段执行
4. 每个阶段进入前, 执行 CLAUDE.md 的思维协议 (定义→发散→追问→收敛)

Path B+ 的 P 阶段可用: `/plan {design.md 一句话摘要}` 快速进入规划
