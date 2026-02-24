---
name: vibe-dev
description: 统一开发入口 — 接收需求后自动触发 PACE 路由
allowed-tools: Read, Write, Edit, Bash, augment-context-engine, cunzhi, mcp-deepwiki
---

# /vibe-dev

1. 接收需求 → `augment-context-engine` 搜相关代码
2. 读 `workflows/pace.md` → 判定 Path (A/B/C/D)
3. Path A → CLAUDE.md 快速通道
4. Path B+ → 读 `skills/plan-first/SKILL.md` → 先出计划
5. 读 `workflows/riper-7.md` → 从 R 阶段开始
6. 创建/更新 `.ai_state/session.md` (需求、Path、阶段)
7. 检查 `.ai_state/requirements/` 和 `assets/` 有无参考资料
