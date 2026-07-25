# Claude Review Repair Evidence — Athena 9.9.6

Date: 2026-07-25  
Stage: impl  
Release status: draft, not released

## Scope

- Fixed confirmed P0s: fresh CX empty base URL, forced-background CC review agents, missing CX spawn PreToolUse gate.
- Fixed structural/security drift: runtime skill fence, hook docs, evaluator precedence, npx boundaries, critic count, manual alias wording, CX provenance, JSON formatting.
- Scoped GPT-5.6 gateway risk to the Azure 0.144.0 reproduction in openai/codex#31882; other gateways remain dogfood obligations, not proven failures.
- Did not add a CC CHANGELOG or treat model metadata precedence as a confirmed bug.

## TDD evidence

Initial focused scan was red:

- `openai_base_url = ""` present.
- reviewer and spec-compliance both contained `background: true`.
- no CX `spawn_agent|Agent` PreToolUse matcher.
- unsafe `Bash(npx playwright*)` and `Bash(npx ecc-agentshield*)` rules present.
- CC runtime-verify SKILL had an odd fence count.

After repair:

```text
PYTHONDONTWRITEBYTECODE=1 python3 vibeCoding/scripts/validate-athena-9.9.6.py
SUMMARY pass=63 fail=0 skip=0
```

The validator covers complete-fork/package parity, 26-skill parity, JSON/TOML/frontmatter/fence checks, fresh and same-version setup, exact Codex 0.145 `config.load`, all six historical F-series scripts, CX spawn block/allow fixtures, audit recording, ship rejection of actual violations, and acceptance of explicit remediation evidence.

Additional checks:

```text
config parse PASS
python compile PASS
git diff --check: clean
legacy bad-pattern scan: no hits outside REVIEW-9.9.6.md
```

Three pre-existing package cache directories were removed: CC setup `__pycache__`, CX setup `__pycache__`, and CX hooks `__pycache__`. They were disposable generated artifacts.

## Remaining release obligations

- F1-F6 local invocation/state/runtime/eval work remains pending.
- Exact-host full PACE dogfood must still verify GPT-5.6 Sol `code_mode_only` Bash/apply_patch hook dispatch and the configured gateway.
- Formal runtime-verify, 2+1 review, polish, architecture finalization and separate ship authorization remain mandatory.
- No commit, push, or release was performed.

## Execution exception

The user explicitly required direct edits in the original checkout. A temporary worktree/branch was removed before any agent was bound or wrote files. Three bound execution attempts (`generator`, `worker`, `default`) all reported that their task contexts exposed no shell/filesystem tools and made zero file changes; the main thread then implemented the authorized repair in the current checkout.
