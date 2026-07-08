# Review Pass 1 — F1 Orchestrator Framework Design

- Sprint: `2026-07-07-f1-orchestrator-framework-design`
- Path: System
- Review date: 2026-07-08
- Verdict: CONCERNS
- Next action: polish

## Reviewer (代码层 findings)

| Severity | Finding | Resolution |
|---|---|---|
| P0 | Token collector implementation files were untracked and easy to omit from review/commit. | Added explicit review evidence for new collector/test/runtime files; final ship must include them. |
| P0 | Token fingerprint included `stage`, so the same transcript could be counted twice after stage changes. | Fixed: fingerprint excludes `stage`; regression asserts stage-change dedupe. |
| P1 | Token collector had no persistent regression tests. | Fixed: `scripts/test-token-usage-collector.py` covers transcript parsing, empty payloads, SubagentStop, XML usage tags, stage dedupe, and null unknown totals. |
| P1 | Concurrent token writes could race. | Fixed: both CC/CX collectors use lock files plus atomic replace/rename. |
| P1 | `SubagentStop` token usage could be missed because `agent_transcript_path` was unsupported and collector was not registered there. | Fixed: both collectors read `agent_transcript_path`; both CC/CX packages register token collector on `SubagentStop`. |
| P1 | System architecture gate could miss main-worktree changes by checking only `main...HEAD` or `evidence.yaml`. | Fixed: both delivery gates count committed branch diff, staged diff, unstaged diff, and untracked files. Regression added. |
| P2 | Design said delivery-gate changes were out of scope while implementation touched gate behavior. | Fixed: design implementation slice now includes delivery-gate architecture-count hardening. |

## Spec Compliance (spec-compliance, 2026-07-08)

### MISSING (做少了)

- Original concern: checklist wording required “CC transcript 实测”, but no real CC transcript exists on this machine.
- Resolution: checklist/design/runtime evidence now state the accurate scope: official `transcript_path` / `agent_transcript_path` contract plus synthetic JSONL verification. Real CC transcript remains an environment limitation, not fabricated evidence.

### EXTRA (做多了)

- Delivery-gate architecture counting was added beyond the original skeleton-only slice.
- Classification: justified review rework. It directly fixes a P1 System-path ship gate bug found in Round 3.

### DEVIATED (做偏了)

- Original deviation: token output lacked stage x model buckets. Fixed with `by_stage -> model`.
- Original deviation: `<usage>subagent_tokens=...` text blocks were unsupported. Fixed in both collectors.
- Original deviation: runtime env keys conflicted (`frontend/backend/database` vs `fe/be/db`). Fixed: references define canonical keys and aliases.
- Original deviation: checkpoint protocol lacked a mechanical schema. Fixed: references define `checkpoints.yaml` with status, attempt, confirmation, issue, evidence, and rollback fields.
- Original deviation: delivery report schema allowed `0` for unknown token usage. Fixed: schema uses `null` for unknown totals and references `token-usage.yaml`.

### 总评

CONCERNS: implementation and schema deviations are resolved, but real CC transcript coverage is explicitly unavailable in this environment.

## Evidence Cross-Check

| Checklist item | Evidence | Status |
|---|---|---|
| plan | `design-brief.md`, `design.md` | done |
| design-statemachine | `design.md` Decision 1 | done |
| design-checkpoint | `design.md` Decision 2; `checkpoint-protocol.md` | done |
| design-skills-boundary | `design.md` Decision 3; skill package files | done |
| design-report-schema | `delivery-report-schema.md` | done |
| design-token-hook | CC/CX collectors, hook config, `runtime-verify.md`, `scripts/test-token-usage-collector.py` | done with CC real-transcript limitation |
| design-runtime-env | `runtime-env-contract.md` canonical schema | done |
| design-dual-platform | CC/CX hook matrix and package parity check | done |
| critic | `design.md` Critic Findings Round 1/2/3 and this pass | done |
| skeleton | CC/CX skill package plus registered Codex skills from prior skeleton commit | done |

## Validation Evidence

| Command | Result |
|---|---|
| `python3 scripts/test-token-usage-collector.py` | `token usage collector regression ok` |
| `python3 scripts/test-delivery-gate.py` | `delivery gate regression ok` |
| `python3 -m py_compile vibeCoding/codex/9.9.0/.codex/hooks/token-usage-collector.py vibeCoding/codex/9.9.0/.codex/hooks/delivery-gate.py scripts/test-token-usage-collector.py scripts/test-delivery-gate.py` | exit 0 |
| `node --check vibeCoding/claude/9.9.0/.claude/hooks/token-usage-collector.cjs && node --check vibeCoding/claude/9.9.0/.claude/hooks/delivery-gate.cjs` | exit 0 |
| JSON parse of `hooks.json` and `settings.json` | parsed both files |
| `diff -qr vibeCoding/codex/9.9.0/.codex/skills/biz-delivery-loop/references vibeCoding/claude/9.9.0/.claude/skills/biz-delivery-loop/references` | no output |
| `git diff --check` | exit 0 |

## Official References

- Codex hooks: https://developers.openai.com/codex/hooks
- Claude Code hooks: https://code.claude.com/docs/en/hooks

## Evaluator Verdict

CONCERNS. Proceed to polish, preserving the explicit limitation that real CC transcript evidence was not available locally. Do not ship until `cleanup-pass.md`, architecture docs, and final delivery gate checks are complete.
