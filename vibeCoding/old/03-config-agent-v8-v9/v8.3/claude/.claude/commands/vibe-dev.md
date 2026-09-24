---
name: vibe-dev
description: 统一开发入口 — 接收需求后自动触发 PACE 路由, 进入 RIPER-7 流程
allowed-tools: Read, Write, Edit, Bash, augment-context-engine, cunzhi, mcp-deepwiki
---

# /vibe-dev — 开始开发

## 流程

1. 接收用户需求描述
2. `augment-context-engine` 快速搜索相关代码
3. 读 `workflows/pace.md` → 判定 Path (A/B/C/D)
4. 如果 Path A → 直接进入 CLAUDE.md 快速通道
5. 如果 Path B+ → 读 `workflows/riper-7.md` → 从 R 阶段开始
6. 创建/更新 `.ai_state/session.md`:
   ```markdown
   ## 会话 {日期}
   需求: {用户原话}
   Path: {判定结果}
   阶段: R (Research)
   ```

## 注意

- 先调用官方 `/dev` 命令 (如可用), 再叠加 VibeCoding 编排
- 不跳过 PACE 判定, 不自作主张选 Path
- 不确定时默认 Path B, 不要默认 Path A
