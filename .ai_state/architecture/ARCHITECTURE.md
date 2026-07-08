---
last_updated: "2026-07-08"
triggered_by_sprint: "2026-07-07-f1-orchestrator-framework-design"
state: "current"
---

# Rlues Athena Package Architecture

## 一句话

Rlues stores versioned Athena/VibeCoding distribution packages for Claude Code and Codex. The `vibeCoding/claude/9.9.0/.claude` and `vibeCoding/codex/9.9.0/.codex` trees are source-of-truth package copies; installed user-level configs are downstream artifacts.

## 组件总览

```mermaid
graph TD
    Repo["Rlues repo"] --> ClaudePkg["vibeCoding/claude/9.9.0/.claude"]
    Repo --> CodexPkg["vibeCoding/codex/9.9.0/.codex"]
    ClaudePkg --> CCHooks["Claude hooks"]
    CodexPkg --> CXHooks["Codex hooks"]
    ClaudePkg --> CCSkills["Claude skills"]
    CodexPkg --> CXSkills["Codex skills + config.toml registration"]
    CCHooks --> AIState["project .ai_state"]
    CXHooks --> AIState
    CCSkills --> Sprint["PACE sprint artifacts"]
    CXSkills --> Sprint
```

## 子系统索引

| 子系统 | 档案 | 一句话描述 |
|---|---|---|
| Athena delivery package | `lib-athena-delivery-pack.md` | 9.9.0 fullstack-delivery skills, hooks, and shared schemas for CC/CX |

## 数据流

```mermaid
sequenceDiagram
    participant User
    participant Codex
    participant Package as 9.9.0 Package
    participant State as .ai_state
    User->>Codex: request PACE work
    Codex->>Package: load skills/hooks/reference schemas
    Codex->>State: write sprint artifacts
    Package->>State: hooks update evidence, review, token, gate state
    Codex-->>User: report command evidence and next action
```

## 边界

- 不做: target project source generation inside Rlues itself.
- 不做: installed `~/.claude` / `~/.codex` mutation unless user explicitly asks.
- 不做: token usage estimation when hook payloads/transcripts lack usage fields.

## 关键决策

- Token usage unknown totals use `null`, not `0` -> `compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md`
