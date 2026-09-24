# F6 Review Prompts

Subagents were unavailable due usage limit. The user explicitly authorized main-thread fallback: "自己写出提示词, 指代自己的去写". These prompts are the self-directed substitute; no subagent execution is claimed.

## Reviewer Prompt

Review sprint `2026-07-08-f6-end-to-end-drill` for correctness, security, test integrity, design fit, and quality. Check `plan.md`, `design.md`, `runtime-verify.md`, `scripts/test-end-to-end-drill.py`, and the command evidence. Flag any place where static validation is overstated as dynamic E2E.

## Spec Compliance Prompt

Compare F6 design acceptance criteria with the actual files and command results. Classify MISSING, EXTRA, and DEVIATED. Pay special attention to dynamic blockers: backend runtime-env, OAuth/test accounts, and cowork remote fetch.

## Evaluator Prompt

Combine reviewer and spec-compliance findings. Decide PASS, CONCERNS, REWORK, or FAIL. PASS is allowed only if the final wording says static contract drill passed and live dynamic E2E is blocked, not complete.
