---
sprint_slug: "2026-09-20-evidence-pipeline-integrity"
path: "System"
stage: "design"
author: "cc-main (revised twice: design reviews 09eec6bf and 1baf009c, both CONCERNS)"
base_commit: "52ff57eb68965ff2738d9e49bbbf95994b311f48"
---

# Evidence pipeline integrity

## WHY

A recorded `result: pass` claims the classified validation command succeeded. Today it only claims the *shell line* exited zero, and those are different statements.

- A pipeline returns the last element's status, so `npm test 2>&1 | tail -8` reports success while tests fail. GNU Bash: <https://www.gnu.org/software/bash/manual/html_node/Pipelines.html>
- `||`, `;` and `&` mask failure identically: `npm test || true`, `npm test; echo done` and `npm test &` all exit zero with failing tests, and `pipefail` helps none of them. Roadmap row 4 asks for provable first-segment exit semantics, not a pipe-only patch.
- On CC the gap is wider: the Bash `tool_response` carries no `exit_code`, so `evidence-collector.cjs:49-53` infers exit 0 from a non-interrupted `PostToolUse`. That inference is right about the line and wrong about the command.

A `tail`/`tee` allowlist would keep every one of these open, because it uses the shape of the last element as proof about the first.

## HOW

### Scope decision: new module, guard untouched

The first review objected to writing a second lexer beside the guard's tokenizer (P0 DRY). The second review established that extracting the guard's tokenizer cannot work here: neither platform emits `&` as an operator (`pre-bash-guard.cjs:140-143`, `pre-bash-guard.py:182-185`), CX's `split_segments` is not quote-aware at all, and adding either capability changes real guard decisions — `echo hi & rm -rf /` is allowed today precisely because `&` is not an operator.

So this slice adds `_shell-lex` as a **new** module consumed only by the evidence policy, and does **not** modify `pre-bash-guard`. Consequences, stated rather than discovered later:

- No guard decision changes in this slice, so there is nothing to characterize or risk.
- Two scanners coexist temporarily. This is scheduled debt with a named owner: slice 8 (`heredoc-aware-shell-guard`) must already rewrite the guard's scanner for heredocs, and converges it onto `_shell-lex` then. Record in the roadmap that slice 8 now follows slice 2 on these files.
- `_shell-lex` is written correct-by-construction for both platforms rather than inheriting CX's quote-blindness, which is what makes CC/CX verdict parity reachable at all.

### `_shell-lex`: quote-aware control-operator scan

One module per platform exposing the segment structure the policy needs. Quote and backslash aware, so an operator character inside `'…'` or `"…"` is ordinary text.

Control operators recognized: `;`, `&&`, `||`, `|`, `|&`, `&`, newline. The `&` rules carry the sharp edges:

- `&` is a control operator only when it is not part of `&&`, and not part of a redirection: `2>&1`, `>&2`, `<&0`, `&>file`, `&>>file`, and `|&` are not backgrounding.
- This matters for AC1's own canonical command: a naive split turns `npm test 2>&1 | tail -8` into `[npm test 2>] & [1] | [tail -8]`, which would push the validation out of the final pipeline and wrongly reject it.

The scanner returns segments plus the operator that follows each. It does not build an AST, expand anything, or interpret heredocs.

### Provability rule

`validationStatusPolicy(command)` sits beside `classifyValidation` in the input-binding module and returns admissibility plus a reason. Because `classifyValidation` is whole-string and returns one kind, the policy **re-runs it per segment**; its `COMMAND_PREFIX` already anchors on `^` so an isolated segment matches.

An observed exit 0 proves a validation segment V succeeded exactly when every path to exit 0 runs V successfully. That gives three conditions, all required:

1. **V's own status reaches its pipeline's status.** V is the last segment of its pipeline, or `pipefail` is enabled at V.
2. **V's pipeline reaches the line's status.** Every control operator between V's pipeline and end of line is `&&`. Bash propagates a left-hand failure through `&&`, so `npm test && echo ok` is provable; `;` and `||` are not, because exit 0 can come from the right-hand side.
3. **The line is not backgrounded.** A trailing `&` reports the shell's status, not V's.

Conditions are evaluated 3 → 2 → 1 and the first failure supplies the reason. The order is normative, not incidental: two matrix rows fail more than one condition (`npm test | tail -8 || echo done`, `npm test &`), and AC3 demands identical reasons from two independent implementations.

The whole command string counts as one line for condition 2, with newline behaving exactly like `;`. CC's Bash tool routinely carries multi-line commands, and a per-line reading would call `npm test` on line 1 provable while the observed exit 0 came from line 2.

If no segment classifies as validation, the record keeps today's semantics. The "every segment" quantifier is vacuously true on an empty set and must not be read as licence to downgrade.

`pipefail` state at V: scan every `set` statement before V in order. `-o pipefail` or `-<flags>o pipefail` (`-eo`, `-euo`, `-euxo`, …) enables; `+o pipefail` or `+<flags>o pipefail` disables; `set` statements mentioning neither are ignored, so `set -o pipefail; set -e; npm test | tail -8` stays admissible. Bash set builtin: <https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html>

If a line holds several classified validation segments, every one must satisfy all three conditions. Under rule 2 this is consistent: in `npm run lint && npm test` the `lint` segment reaches the line's status through `&&`, so both segments are provable.

Full expected matrix, which is also the test matrix:

| Command | Provable | Reason when not |
|---|---|---|
| `npm test` | yes | |
| `npm run lint && npm test` | yes | |
| `npm test && echo ok` | yes | |
| `set -o pipefail; npm test 2>&1 \| tail -8` | yes | |
| `set -o pipefail; set -e; npm test \| tail -8` | yes | |
| `set -euo pipefail; npm test \| tee test.log` | yes | |
| `go test -run 'A\|B' ./...` | yes | |
| `pytest -k "a\|b"` | yes | |
| `npm test \| tail -8` | no | `pipeline_without_pipefail` |
| `set -o pipefail; set +o pipefail; npm test \| tail -8` | no | `pipeline_without_pipefail` |
| `npm test \|\| true` | no | `validation_status_not_reported` |
| `npm test; echo done` | no | `validation_status_not_reported` |
| `npm test \| tail -8 \|\| echo done` | no | `validation_status_not_reported` |
| `npm test &` | no | `validation_backgrounded` |

The reason enum is exactly those three values, pinned because AC3 requires identical reasons on both platforms.

### What the collector does with it

- Pre-hook capture is unchanged: every recognized validation command is still snapshotted, including non-provable ones, so an auditable record always survives.
- On a non-provable command a **nominal success** becomes `result: unknown` plus one line `result_reason: "<enum>"`. The key is a hardcoded literal because CC emits evidence keys unescaped (`evidence-collector.cjs:71`); only the value uses the existing JSON escaper.
- `result_reason` is a separate axis from `binding_status: unverifiable`, which stays reserved for input drift. One record may carry both.
- An **observed failure stays `fail`** on every path. Downgrading a real failure would destroy trustworthy evidence.
- Provable commands keep their current status semantics byte for byte.
- No delivery-gate edit: both gates read evidence by named field, ignore unknown keys, and already refuse to ship on `unknown` alone. This also keeps the slice clear of the serialized gate slices 5 and 6.
- CX truncates the persisted command at 120 characters against CC's 500. Raise CX to 500 so a `set -o pipefail` prefix or the pipe survives into `evidence.yaml` and the verdict stays auditable; AC3 asserts it.

### Platform reach and load failure

`pi-agent/plugin/extensions/cc-core/_input-binding.cjs` is a byte-identical live copy of the CC file, executed through `athena-gates.ts`, so Pi receives the binding change and the new `_shell-lex.cjs`. Pi's `pre-bash-guard.cjs` is untouched and stays identical by construction. Pi has no `evidence-collector`, so the collector half does not apply.

Byte-identity is asserted for an explicit file list — `_shell-lex.cjs`, `_input-binding.cjs`, `pre-bash-guard.cjs` — not directory-wide: `cc-core/delivery-gate.cjs` and `cc-core/session-start.cjs` already diverge from their CC originals for unrelated reasons.

The new `require` must not put the delivery gate on its load path. `_input-binding` is required at module top level, with no `try`, by `delivery-gate.cjs:15`, `evidence-collector.cjs:7`, `_review-binding.cjs:4`, the Pi copies of the first and third, and CX `delivery-gate.py:28`. A module-load `require` of `_shell-lex` would therefore throw at *gate import*, before any fail-closed logic runs: CC treats exit 1 as non-blocking, Pi maps any non-2 exit to allow (`athena-gates.ts:42-43`), and CX emits no block JSON. That turns the ship gate from fail-closed into silently permissive. `setup-athena.py`'s `REQUIRED_ASSETS` (`:136-148`) cannot list a module it predates, so `managed_complete` would call a broken home complete and the repair path would never fire.

`validationStatusPolicy` therefore requires `_shell-lex` **lazily, inside the function**, and treats a load failure as non-provable. Evidence fails closed, and no gate ever loads the module. AC5 pins this with a regression rather than an assertion.

## Acceptance Criteria

- [ ] AC1: On CC and CX, `set -o pipefail; npm test 2>&1 | tail -8` and `set -euo pipefail; npm test | tee test.log` are classified as test evidence and record a current PASS through the real pre-bash-guard → evidence-collector chain; an observed failure of the same command records `fail`.
- [ ] AC2: No collector-written record reaches `result: pass` when the validation command's status is masked. `npm test | tail -8`, `npm test || true`, `npm test; echo done`, `npm test &` and `npm test | tail -8 || echo done` each record `unknown` with the matching `result_reason` on nominal success, and `fail` when a failure is observed.
- [ ] AC3: The full matrix above yields identical verdicts and identical reasons on CC and CX, including quoted pipes (`go test -run 'A|B' ./...`, `pytest -k "a|b"`), `&&` chains, redirections (`2>&1`, `&>`, `|&`), `set` enable/disable ordering, and an intervening `set -e`; CX persists the command at the same 500-character bound as CC so the verdict stays auditable from `evidence.yaml`.
- [ ] AC4: The CC leg is exercised with a CC-shaped response carrying no `exit_code` (`{stdout, stderr, interrupted: false}`) plus a `PostToolUseFailure` leg for the failure half, so the production failure mode is actually covered; long redacted output still preserves the trailing test summary, and no second summary mechanism or duplicate collector path is introduced.
- [ ] AC5: `pre-bash-guard` is byte-identical before and after this slice on all three platforms, asserted by `git diff --exit-code 52ff57eb -- <the three guard paths>`, proving no guard decision changed; the Pi `cc-core` copies of `_shell-lex.cjs`, `_input-binding.cjs` and `pre-bash-guard.cjs` are byte-identical to their CC originals, asserted by test over that explicit list; and with `_shell-lex` removed, the delivery gate still blocks instead of failing open.
- [ ] AC6: CC, CX and Pi gate contracts document the copyable `set -o pipefail; npm test 2>&1 | tail -8` and state that an unprotected pipeline, a masked validation command, or a backgrounded one is not admissible evidence.

## File Structure Plan

- `vibeCoding/claude/9.9.9/.claude/hooks/_shell-lex.cjs`: new; quote-aware control-operator scanner.
- `vibeCoding/claude/9.9.9/.claude/hooks/_input-binding.cjs`: `validationStatusPolicy` beside `classifyValidation`.
- `vibeCoding/claude/9.9.9/.claude/hooks/evidence-collector.cjs`: downgrade non-provable nominal success with `result_reason`.
- `vibeCoding/codex/9.9.9/.codex/hooks/_shell_lex.py`, `_input_binding.py`, `evidence-collector.py`: Python equivalents, including the 120 → 500 command bound.
- `vibeCoding/pi-agent/plugin/extensions/cc-core/_shell-lex.cjs`, `_input-binding.cjs`: byte-identical copies of the CC files.
- CC, CX and Pi `skills/pace/references/gate-contracts.md`: operator contract and copyable command.
- `vibeCoding/scripts/tests/athena999/test_state_review.py`: policy matrix on both platforms, real-chain CC/CX legs, guard byte-identity, Pi parity, and the #13 redaction regression.
- `.ai_state/roadmap/q12-batch2-production-gaps/roadmap.md`: record that slice 8 now follows slice 2 and owns the scanner convergence.
- `.ai_state/architecture/ARCHITECTURE.md`, `.ai_state/architecture/athena-9.9.8.md`: evidence contract update at polish.

## Non-goals

- No shell AST, heredoc handling or `PIPESTATUS` inspection; heredocs are slice 8, which also converges the two scanners.
- No modification of `pre-bash-guard` in this slice; AC5 pins that as a byte-level invariant.
- No inference of inherited shell options or wrapper state. An unproven command is downgraded, never guessed.
- `set` statements are counted lexically, not by reachability, so `false && set -o pipefail` reads as enabling. This is the one place the rule errs toward admitting rather than downgrading; a reachability analysis is not worth its cost here.
- No delivery-gate edit, no new config flag, no skip switch.
- No PreToolUse command rewriting to inject `pipefail`; the agent stays responsible for the command it reports.
- Hand-written evidence records are out of scope; every binding field is agent-computable, so forged records are slice 5's provenance problem.
- No installation into `~/.claude` or `~/.codex`; package source only.
