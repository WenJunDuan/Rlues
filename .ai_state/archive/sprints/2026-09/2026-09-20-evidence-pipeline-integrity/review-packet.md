---
source_design_sha256: "5b78c2f29e3fa8a7fbd0a4739f55944fa01e0c6bdf5a8e344d72bd8d71dba4f4"
mode: "design"
---

# Review Packet — evidence pipeline integrity

## Decision

`result: pass` must mean the classified validation command succeeded, not that the shell line exited zero. A validation segment is provable only when its status reaches its pipeline's status (last position or `pipefail`), its pipeline reaches the line's status (only `&&` in between), and the line is not backgrounded. Everything else downgrades to `unknown` with a pinned reason; observed failures always stay `fail`.

## Acceptance mapping

| AC | Mechanism | Verification |
|---|---|---|
| AC1 | per-segment classifier + pipefail-protected pipeline admitted | real hook chain on CC/CX; success and observed-failure legs |
| AC2 | three-condition provability rule; pass-only downgrade + reason | pipe, `\|\| true`, `;`, `&`, pipe-then-`\|\|` matrix, both outcomes |
| AC3 | new quote-aware scanner written for both platforms; ordered `set` scan | full matrix verdict **and** reason equality; quoted pipes, `&&`, redirections, enable→disable; CX command bound raised to 500 |
| AC4 | CC-shaped payload without `exit_code` + PostToolUseFailure; existing head/tail redaction | production failure mode covered; summary tail retained; no second summary path or duplicate collector |
| AC5 | guard not modified; lazy `_shell-lex` require; Pi copies over an explicit file list | `git diff --exit-code` on three guard paths; Pi parity over three named files; gate still blocks with `_shell-lex` removed |
| AC6 | three platform contract copies | exact text parity assertions |

## Challenge points

- Admitting `tail`/`tee` by name uses the last element's shape as proof about the first, so the allowlist route is rejected outright.
- Pipe-only scope leaves `\|\| true`, `;` and `&` masking open; roadmap row 4 asks for first-segment exit semantics, so the rule is segment-based.
- Extracting the guard's tokenizer was tried and rejected on evidence: neither platform emits `&`, CX's splitter is quote-blind, and adding either changes live guard decisions (`echo hi & rm -rf /` is allowed today only because `&` is not an operator). A new module leaves the guard untouched; slice 8 already rewrites the guard's scanner for heredocs and converges them there.
- `&&` must stay provable: bash propagates a left-hand failure through it, so downgrading `npm test && echo ok` would block a correct command.
- Naive `&` splitting breaks AC1's own command by cutting `2>&1`; the scanner must exclude redirection forms.
- Real non-zero results must never become `unknown`; only nominal success is downgraded.
- CC's Bash response has no `exit_code`, so tests feeding `exit_code: 0` to both platforms never touch the production failure path.
- `#13` head/tail redaction already exists on both ends and receives regression coverage only.
- A module-load require of `_shell-lex` would put the ship gate on its load path; `delivery-gate` requires `_input-binding` at top level with no `try` on all three platforms, and every platform maps a load failure to allow. The require is therefore lazy inside the policy, and a load failure yields non-provable.
- Reason precedence is normative (3 then 2 then 1); two matrix rows fail more than one condition and AC3 demands reason equality.
- Forged hand-written evidence stays out of scope; that is slice 5's provenance receipt.

## Allowed write set

Only the implementation, tests, three contracts, the roadmap ordering note, architecture files and current sprint artifacts listed in the design File Structure Plan. `pre-bash-guard` is explicitly excluded.
