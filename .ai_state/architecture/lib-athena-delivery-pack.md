---
type: lib
slug: athena-delivery-pack
last_updated: "2026-07-10"
triggered_by_sprint: "2026-07-10-athena-9-9-1-validation"
---

# Library: Athena Delivery Pack

## 角色

This subsystem packages Athena 9.9.1 for Claude Code and Codex. It keeps shared PACE/skill semantics aligned, preserves platform-specific hook/config implementations, and treats setup, migration, runtime evidence, and release validation as one audited delivery surface.

## 组成

- Current CC package: `vibeCoding/claude/9.9.1/.claude`
- Current CX package: `vibeCoding/codex/9.9.1/.codex`
- Immutable upgrade baseline: `vibeCoding/{claude,codex}/9.9.0`
- Shared skills: `scaffold-page-gen`, `db-schema-gen`, `unit-test-gen`, `security-test`, `playwright-e2e`, `biz-delivery-loop`
- Existing integrated skills: `scaffold-module-gen`, `project-data-reader`
- Hook family: token usage collectors, delivery gates, subagent/worktree/evidence trackers
- Release harness: `vibeCoding/scripts/validate-athena-9.9.1.py`, runtime fixtures, setup/migrate behavior suites
- Transaction orchestrator: `athena-migrate/scripts/migrate-9.9.0-to-9.9.1.py`

## 接口

### 对外提供

- Codex skill registration through `vibeCoding/codex/9.9.1/.codex/config.toml`; user skills install to `~/.agents/skills`.
- Claude/Codex package files that can be copied into user-level config directories.
- Fresh setup for missing endpoints and a targeted dual-end 9.9.0→9.9.1 transaction migration.
- PACE reference contracts under `biz-delivery-loop/references/`, including orchestration, checkpoints, runtime-env, and delivery-report schemas.
- Capability Manifest validation for runtime-only reads through `project-data-reader`.

### 对外依赖

- Project-local `.ai_state/_index.md` as the single state authority.
- Sprint artifacts under `.ai_state/sprints/{slug}/`.
- Official hook payload contracts for Codex and Claude Code.
- Codex 0.144.1 model catalog, hook schemas, multi-agent v2 identity surface, and skill loader behavior.

## 数据模型

- `token-usage.yaml`: sprint-local token usage accumulator. Unknown totals are `null`.
- `runtime-env`: canonical keys are `frontend`, `backend`, `database`; aliases `fe`, `be`, `db` are read-compatible only.
- `checkpoints.yaml`: machine/human checkpoint state with status, attempt, evidence, confirmation, issue path, and rollback target.
- `delivery-report.md`: machine-readable frontmatter plus human-readable Markdown, including token usage status, runtime-env warnings, blocked dynamic cases, and capability read evidence.
- `Capability Manifest`: JSON contract for MCP-backed read-only runtime data access; write capabilities and embedded secrets are rejected before use.
- `subagent-events.jsonl`: raw Start/Stop lifecycle identity from the platform; no inferred task role or exit status.
- `subagent-assignments.jsonl`: main-thread binding from canonical task name/role to the unique raw `agent_id`.
- `evidence.yaml`: explicit pass/fail/unknown results; unknown-only evidence cannot satisfy ship.

## 关键流程

1. PACE stage loads relevant skill instructions.
2. Implementation writes package files and sprint artifacts.
3. Setup or migration preflights every selected endpoint, stages configs/assets, and rolls the whole transaction back on failure.
4. Runtime verification runs real commands or synthetic fixtures where the real platform transcript is unavailable.
5. Review records reviewer/spec results in `reviews/passN.md`, then the evaluator checks merged evidence.
6. Polish updates cleanup, compound, and architecture artifacts before ship.
7. The release validator verifies schemas, behavior, parity, immutable baseline, isolated HOME setup, strict doctor, and prompt discovery.

## 配置项

- `hooks.json` controls Codex hook commands.
- `settings.json` controls Claude Code hook commands.
- `config.toml` controls Codex skill discoverability.
- Codex defaults use the built-in `openai` provider, `gpt-5.6-sol`, and `xhigh`; model context remains catalog-owned.

## 约束与例外

- CC/CX reference docs must stay in parity unless a platform difference is explicitly documented.
- Best-effort collectors fail open; delivery gates fail closed inside Athena projects when required state is absent, malformed, failed, or unknown-only.
- Codex same-event hook order must not be used as a correctness dependency.
- Native v2 spawn returns task identity while lifecycle hooks provide raw `agent_id`; the main thread owns the serial binding handshake and all review/state file writes.
- Setup/migrate preserve provider, MCP, project, plugin, private hook, third-party skill, and unknown user fields; hook trust is never forged or edited.
- `project-data-reader` does not generate code and does not enforce permissions locally; target systems own identity, role, row-level data permission, redaction, and audit.

## 演进历史

- 2026-07-08: Added token usage collectors and SubagentStop coverage -> `compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md`
- 2026-07-08: Added F5 orchestration contract, delivery-report runtime read fields, and Capability Manifest read-only validator.
- 2026-07-10: Released 9.9.1 for Codex 0.144.1 with truthful hook evidence, native multi-agent binding, fail-closed gates, official skill paths, and transactional dual-end migration.
