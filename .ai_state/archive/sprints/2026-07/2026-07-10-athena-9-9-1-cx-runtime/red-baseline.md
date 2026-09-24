# TDD Red Baseline — Athena 9.9.1 CX Runtime

- Command: `python3 vibeCoding/scripts/validate-athena-9.9.1.py`
- Evidence: exec chunk `0b0060`
- Exit: `1` (expected red)
- Summary: `pass=3 fail=29`
- Preserved invariant: `git diff 5eb6189 -- vibeCoding/codex/9.9.0 vibeCoding/claude/9.9.0` passed.

## Red contracts

- portable config: provider/model/context/compact/NUX/version
- hook wire: `tool_response`, no `tool_output`, unknown-safe status
- gate: assignment/event JSONL, final PASS, seven negative cases
- SessionStart: `clear`
- native collaboration: no `spawn_agent --cwd` / `assign_task` / bare `wait`
- current sprint paths: no non-migrate `.ai_state/details`
- skill frontmatter: 22 invalid CX skills
- setup/migrate: AGENTS, repo-root discovery, five states, 9.9.0→9.9.1

Official-source follow-up changed expected CLI model from generic `gpt-5.6` to catalog slug `gpt-5.6-sol`, and CX user skill target from deprecated `$CODEX_HOME/skills` to `~/.agents/skills`; the same validator will prove green after implementation.
