# Runtime Verify — F1 Fullstack Delivery Skills Framework

- Sprint: `2026-07-07-f1-orchestrator-framework-design`
- Path: System
- Stage verified: impl
- Date: 2026-07-07

## /goal 完成条件

1. Token usage collector exists for both CX and CC packages.
2. Stop/SubagentStop hook config wires the collector as a non-blocking command with no delivery-gate ordering dependency.
3. Collector syntax/config validation passes.
4. Collector can parse transcript-style `token_count` JSONL and `agent_transcript_path` SubagentStop fixtures.
5. Real current Stop-style payload with no usage fields records `no_usage_found` instead of invented numbers.
6. Delivery-gate architecture file counting includes main-worktree unstaged/staged/untracked files, not only `main...HEAD`.

## 测试场景 (实跑)

| 场景 | 类型 | 命令 | 实际输出 | 判定 |
|---|---|---|---|---|
| CX collector syntax | compile | `python3 -m py_compile vibeCoding/codex/9.9.0/.codex/hooks/token-usage-collector.py` | exit 0, no stderr | PASS |
| CC collector syntax | syntax | `node --check vibeCoding/claude/9.9.0/.claude/hooks/token-usage-collector.cjs` | exit 0, no stderr | PASS |
| Hook config parse | config | `python3 - <<'PY' ... json.loads(hooks.json/settings.json)` | `json parsed: vibeCoding/codex/9.9.0/.codex/hooks.json`; `json parsed: vibeCoding/claude/9.9.0/.claude/settings.json` | PASS |
| Whitespace safety | diff | `git diff --check` | exit 0, no output | PASS |
| Transcript fixture parse | runtime | temp `.ai_state` + temp JSONL with `payload.type=token_count`; run both collectors | `status: "ok"`, `calls: 2`, `input_tokens: 200`, `output_tokens: 60`, `total_tokens: 260` | PASS |
| Idempotent empty payload | runtime | run CX collector with transcript fixture, then run it again with only `{"hook_event_name":"Stop"}` | existing `records:` kept; `status: "ok"`; `input_tokens: 100` remains | PASS |
| Current sprint no-usage truth | runtime | `printf '{"cwd": ".../Rlues","hook_event_name":"Stop"}' \| python3 .../token-usage-collector.py` | `token-usage.yaml` has `status: "no_usage_found"` and note `keep token totals unknown` | PASS |
| Token collector regression | runtime | `python3 scripts/test-token-usage-collector.py` | `token usage collector regression ok` | PASS |
| Delivery gate changed-file regression | runtime | `python3 scripts/test-delivery-gate.py` | `delivery gate regression ok` | PASS |

## 自测自改记录

- First synthetic run wrote fake token totals into the real sprint file. Fixed by deleting that synthetic output and generating a real `no_usage_found` file from an empty Stop-style payload.
- First collector version could overwrite existing totals when a later Stop payload had no usage. Fixed by parsing existing `records` and rewriting totals from existing + new deduped records.
- Python timestamp used deprecated `datetime.utcnow()`. Replaced with timezone-aware `datetime.now(dt.UTC)`.
- Review found that Codex same-event command hooks cannot be used as a strict order guarantee. Fixed by making collector semantics independent from delivery-gate ordering.
- Review found SubagentStop transcript coverage missing. Fixed by supporting `agent_transcript_path` and registering both package collectors on `SubagentStop`.
- Review found architecture gate could miss main-worktree diffs. Fixed by counting committed branch diff, staged diff, unstaged diff, and untracked files.

## Reflect

- CX current Stop payload did not expose usage or transcript path in this local test, so the real sprint token totals are intentionally unknown.
- The parser is verified against transcript-style `token_count` JSONL, matching observed Codex session JSONL shape from local archived sessions.
- CC real transcript was unavailable on this machine, so CC coverage is by official `transcript_path` / `agent_transcript_path` hook contract plus synthetic JSONL parser verification.
- Codex collector and delivery-gate may run concurrently on Stop; correctness does not require the token file to exist before delivery-gate.
- Remaining process work: formal critic/review, polish, and ship gates are still pending.

## VERDICT

PASS for token hook implementation/runtime verification. Proceed to review.
