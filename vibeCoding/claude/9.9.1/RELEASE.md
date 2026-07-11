# Athena Claude Code 9.9.1

Patch baseline: committed `claude/9.9.0/.claude` tree `eb1ab06bae8e9a9bd576643e941c4e5d59360fb1`.

## Compatibility

| Level | Claude Code | Contract |
|---|---:|---|
| Compatibility floor | 2.1.203 | Core hooks, agents, PACE state and native worktree strong isolation (`isolation: worktree`) |
| Release validation target | 2.1.206 | Full settings/hooks/subagent contract |

The floor moved from 2.1.197 to 2.1.203 (design §18.2) because every supported
version now claims native strong red-zone worktree isolation; the
2.1.197–2.1.202 manual-worktree degradation path is removed.

## Patch changes

- Main model `best` (Fable5 where the org has access, otherwise latest Opus), persisted effort `xhigh`, fallback chain `opus → sonnet`.
- No global subagent model override or default provider/model-ID pins.
- Role models and limits live in seven agent frontmatters; read-only roles use plan mode and deny Write/Edit/Agent.
- Native Git worktree restored with `worktree.baseRef=head`. Default settings do not register WorktreeCreate/Remove because those hooks replace Claude Code's Git implementation.
- PostToolUse and PostToolUseFailure are separate success/failure signals. Missing/unknown events never become passing evidence.
- CC and CX share exact `subagent-events.jsonl` and `subagent-assignments.jsonl` schemas. SubagentStart freezes the sprint; Stop returns to it by `agent_id`.
- Delivery gate is fail-closed for generator lifecycle, checklist, evidence, roadmap, latest numeric passN, PASS-only review, runtime verification, polish and architecture.
- 9.9.0 migration uses a targeted three-way merge and preserves user model choices, private hooks, plugins, MCP/provider/trust fields and secret values.

## Agent Teams

Agent Teams remains experimental and disabled by default. A user may explicitly enable it for System/Refactor research, independent review or mutually exclusive modules. Team tasks are runtime coordination only; `.ai_state/checklist.yaml` remains the source of truth. Do not use nested teams, same-file parallel writers, or team state as a ship dependency.

## Non-Git version control

WorktreeCreate/Remove hooks are appropriate only for SVN, Perforce, Mercurial or another non-Git backend. Keep them in a separate opt-in profile. A WorktreeCreate hook must create the checkout and return its path; registering one for Git disables Claude Code's native worktree creation and `.worktreeinclude` behavior.

## Validation

```bash
node vibeCoding/scripts/test-athena-claude-9.9.1-runtime.cjs
PYTHONDONTWRITEBYTECODE=1 python3 vibeCoding/claude/9.9.1/.claude/skills/athena-migrate/tests/test_migrate_991.py
PYTHONDONTWRITEBYTECODE=1 python3 vibeCoding/claude/9.9.1/.claude/skills/athena-setup/tests/test_setup_991.py
python3 vibeCoding/scripts/validate-athena-9.9.1.py
```

If the `claude` executable and npm registry access are unavailable, the suite reports the 2.1.203/2.1.206 live HOME matrix as skipped with the failure reason. Static payload contracts and a real Git worktree isolation simulation still run; they are not presented as Claude runtime evidence.

Release remains blocked until post-implementation Fable5 review returns PASS and all P0/P1 findings are merged and revalidated.

## Known limitations (pre-bash-guard static analysis)

`pre-bash-guard.cjs` parses the Bash command text structurally (quotes,
comments, `$()`/backtick substitution, wrapper commands) without invoking a
real shell. Two constructs remain outside what static text analysis alone can
resolve safely:

- **`eval $VAR` / `eval "$VAR"` (variable-indirect eval)**: `unwrap()` only
  re-analyzes `eval` when its argument tokens are literal text (e.g.
  `eval "rm -rf /"`); a bare variable reference carries no text to parse
  until the shell substitutes it at runtime, so the guard cannot see what it
  will expand to and lets it proceed unchanged.
- **Process substitution (`<(...)`, `>(...)`)**: `findSubstitutions()` only
  looks for `$(...)` and `` `...` ``; a command like `diff <(git push origin
  main) /dev/null` is not currently walked into, so a dangerous command
  hidden behind process substitution is not analyzed.

Both are static-analysis boundaries, not regressions introduced by this
patch's `#`-comment fix. Mitigation: the guard is one layer of defense in
depth, not the sole gate — `stage != ship` git push is also enforced by the
generator/reviewer workflow discipline, and irreversible destructive actions
still require passing `delivery-gate.cjs` and the permissions system before
`ship`. Track hardening these two cases (recursive re-analysis of `eval`
after best-effort env-var resolution, and adding `<(...)`/`>(...)` spans to
`findSubstitutions`) in the next guard patch.

## Known issue (handoff to next CX patch)

`vibeCoding/codex/9.9.1/.codex/hooks/delivery-gate.py:328` has the same inline-`*`
stripping defect as the CC `finalVerdict` bug fixed in this patch: a review line
like `**判定**: PASS` only has its leading/trailing `*` stripped, leaving
`判定**: PASS`, which fails to match either VERDICT regex and blocks a
legitimate PASS. This CC worktree is scoped to `vibeCoding/claude/9.9.1/**` and
`vibeCoding/scripts/**`; `vibeCoding/codex/9.9.1/**` must not be touched here.
Apply the equivalent fix (strip all `*` from the line before matching, e.g.
`line.replace("*", "")`) in a dedicated CX 9.9.1 patch.

## Official references

- Hooks: https://code.claude.com/docs/en/hooks
- Subagents: https://code.claude.com/docs/en/sub-agents
- Worktrees: https://code.claude.com/docs/en/worktrees
- Settings: https://code.claude.com/docs/en/settings
- Model configuration: https://code.claude.com/docs/en/model-config
- Agent Teams: https://code.claude.com/docs/en/agent-teams
