---
sprint_slug: "2026-09-13-pi-agent-9-10"
path: "Feature"
created: "2026-09-13"
---

# Design — Athena 9.10 Pi 端

> 电宝体。门禁标题勿改。背景≤5行。AC 一句一条。

## 背景 (context)

Pi 端停在 9.9.6 试点。用户要整份 CC 9.9.9 结构（PACE/skills/hooks/agents/rules）迁入 Pi，版本暂定 9.10。不是只搬 AGENTS.md。

## 方案

Pi 原生：`AGENTS.md` + `APPEND_SYSTEM.md` + `skills/` + `prompts/` + `extensions/` + `package.json` `pi` 清单。
CC hook → 适配器调 `extensions/cc-core`（9.9.9 同源）。无 Pi 事件的 hook 原样保留、文档标明未接线。
红区：无 `isolation: worktree` → `git worktree` + 新 pi session / 可选 `pi-subagents`。
不伪造 CC 对称工具。不一次全装社区包。

## 验收标准 (Done Contract)

- [ ] AC1: `vibeCoding/pi-agent/9.10/` 含 skills（含 pace）、rules、cc-core hooks、prompts、AGENTS.md、package.json。
- [ ] AC2: 路径指向 `~/.pi/agent/{skills,rules,extensions/cc-core}`，不残留作为运行路径的 `~/.claude`。
- [ ] AC3: Pi 事件映射成文：tool_call/agent_end/session_start/before_agent_start/compact；未接线 hook 列出。
- [ ] AC4: 啰嗦/精简记录写入本 sprint `verbosity-notes.md`，供下次迭代。

## File Structure Plan

```
vibeCoding/pi-agent/9.10/
```
