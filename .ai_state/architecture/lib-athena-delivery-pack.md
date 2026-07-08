---
type: lib
slug: athena-delivery-pack
last_updated: "2026-07-08"
triggered_by_sprint: "2026-07-08-f5-biz-delivery-loop"
---

# Library: Athena Delivery Pack

## 角色

This subsystem packages reusable Athena 9.9.0 fullstack-delivery behavior for both Claude Code and Codex. It keeps skill procedures, hook scripts, and reference schemas aligned across the two platform package trees while preserving platform-specific runtime implementations.

## 组成

- CC package: `vibeCoding/claude/9.9.0/.claude`
- CX package: `vibeCoding/codex/9.9.0/.codex`
- Shared skills: `scaffold-page-gen`, `db-schema-gen`, `unit-test-gen`, `security-test`, `playwright-e2e`, `biz-delivery-loop`
- Existing integrated skills: `scaffold-module-gen`, `project-data-reader`
- Hook family: token usage collectors, delivery gates, subagent/worktree/evidence trackers

## 接口

### 对外提供

- Codex skill registration through `vibeCoding/codex/9.9.0/.codex/config.toml`.
- Claude/Codex package files that can be copied into user-level config directories.
- PACE reference contracts under `biz-delivery-loop/references/`, including orchestration, checkpoints, runtime-env, and delivery-report schemas.
- Capability Manifest validation for runtime-only reads through `project-data-reader`.

### 对外依赖

- Project-local `.ai_state/_index.md` as the single state authority.
- Sprint artifacts under `.ai_state/sprints/{slug}/`.
- Official hook payload contracts for Codex and Claude Code.

## 数据模型

- `token-usage.yaml`: sprint-local token usage accumulator. Unknown totals are `null`.
- `runtime-env`: canonical keys are `frontend`, `backend`, `database`; aliases `fe`, `be`, `db` are read-compatible only.
- `checkpoints.yaml`: machine/human checkpoint state with status, attempt, evidence, confirmation, issue path, and rollback target.
- `delivery-report.md`: machine-readable frontmatter plus human-readable Markdown, including token usage status, runtime-env warnings, blocked dynamic cases, and capability read evidence.
- `Capability Manifest`: JSON contract for MCP-backed read-only runtime data access; write capabilities and embedded secrets are rejected before use.

## 关键流程

1. PACE stage loads relevant skill instructions.
2. Implementation writes package files and sprint artifacts.
3. Runtime verification runs real commands or synthetic fixtures where the real platform transcript is unavailable.
4. Review records code/spec/evidence findings in `reviews/pass1.md`.
5. Polish updates cleanup, compound, and architecture artifacts before ship.
6. Fullstack delivery loop validators verify contract readiness without starting target project services.

## 配置项

- `hooks.json` controls Codex hook commands.
- `settings.json` controls Claude Code hook commands.
- `config.toml` controls Codex skill discoverability.

## 约束与例外

- CC/CX reference docs must stay in parity unless a platform difference is explicitly documented.
- Hook scripts fail open; delivery gates block only through the documented platform JSON contract.
- Codex same-event hook order must not be used as a correctness dependency.
- `project-data-reader` does not generate code and does not enforce permissions locally; target systems own identity, role, row-level data permission, redaction, and audit.

## 演进历史

- 2026-07-08: Added token usage collectors and SubagentStop coverage -> `compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md`
- 2026-07-08: Added F5 orchestration contract, delivery-report runtime read fields, and Capability Manifest read-only validator.
