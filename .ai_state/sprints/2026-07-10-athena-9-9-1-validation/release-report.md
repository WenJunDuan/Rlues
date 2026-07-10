---
sprint_slug: "2026-07-10-athena-9-9-1-validation"
version: "9.9.1"
base_version: "9.9.0"
base_commit: "5eb6189"
status: "shipped"
created: "2026-07-10"
---

# Release Report — Athena 9.9.1

## 发布物

- Claude Code: `vibeCoding/claude/9.9.1/.claude`
- Codex: `vibeCoding/codex/9.9.1/.codex`
- Release validator: `vibeCoding/scripts/validate-athena-9.9.1.py`
- Runtime fixtures: `vibeCoding/scripts/fixtures/athena-9.9.1/`
- Upgrade path: dual-end `9.9.0 -> 9.9.1` transaction orchestrator

## 兼容性结论

- Codex target: `codex-cli 0.144.1`.
- CX defaults: built-in `openai`, `gpt-5.6-sol`, `xhigh`, catalog-owned context/compaction.
- User skills: `~/.agents/skills`; deprecated `~/.codex/skills` only receives exact Athena legacy cleanup.
- Hooks: PostToolUse reads `tool_response`; raw subagent identity and task assignment use separate ledgers; unknown evidence cannot pass.
- Native collaboration: `spawn_agent` / `send_message` / `followup_task` / `wait_agent`; worktree path is an explicit task boundary.
- Setup/migrate: endpoint-independent fresh setup, targeted config merge, private/third-party preservation, one transaction rollback.

## 验证证据

| Gate | Result |
|---|---|
| Release validator | 65/65 PASS |
| Runtime behavior | 30/30 PASS; 21 negative chains BLOCK |
| Migration behavior | 8/8 per endpoint PASS |
| Official skill validation | 62/62 PASS |
| Static parsers | Python 35, JSON 8, TOML 15, YAML 6, Node 16 PASS |
| Isolated HOME | setup, strict doctor config, prompt discovery PASS |
| Immutable baseline | 9.9.0 zero diff |
| Review | pass2 Reviewer + Spec + Evaluator PASS |
| Polish | READY; junk/cache 0; `git diff --check` clean |

## 官方依据

- Model catalog: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/models-manager/models.json
- PostToolUse schema: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/hooks/schema/generated/post-tool-use.command.input.schema.json
- SubagentStop schema: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/hooks/schema/generated/subagent-stop.command.input.schema.json
- Multi-agent v2: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core/src/tools/handlers/multi_agents_spec.rs
- Skill loader: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core-skills/src/loader.rs#L318-L337

## 环境说明

- 本次发布仓库包，不安装到真实 `~/.codex` / `~/.claude`；避免覆盖用户环境。
- 临时 HOME 无凭据，doctor auth failure 属环境限制；配置加载、provider reachability 与 prompt discovery 已通过。
- 安装后 Codex 会按内容哈希要求用户重新审阅 hook trust；迁移器不会伪造或改写 trust store。

## Ship

- Release commit: `c0cc8ed feat(athena): release v9.9.1 for Codex 0.144.1`.
- Main merge: fast-forward `5eb6189 -> c0cc8ed`.
- Origin push: `main -> origin/main`; post-push ahead/behind `0 0` at `c0cc8ed`.
- Worktree/branch cleanup: `/Users/mi_manchi/workspace/Rlues-athena-9.9.1` removed; `codex/athena-9.9.1` deleted.
- Existing main-worktree changes preserved: `vibeCoding/claude/9.9.0/.claude/settings.json` and pre-compact snapshots were not included in the release commit.
