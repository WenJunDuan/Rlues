# Rework Notes — Athena 9.9.3

## Source findings

1. CX breadcrumb resolves deprecated `~/.codex/skills` instead of installed `~/.agents/skills`.
2. Evaluator allows unresolved over-engineering P1 findings to PASS contrary to final design.
3. M5 harness artifact and CX build spec are missing.
4. Validator protects 9.9.1 instead of the declared 9.9.2 baseline.
5. Breadcrumb total line budget exceeds the declared limit.
6. Release roots contain `.DS_Store`; validation/docs evidence is stale and Codex command failures are misdiagnosed as JSON errors.

## Status

Implementation complete at `8234f0b54852d553469a9126b734fb1820592d92`; CX 67/67、CC 107/107、validator 223/223 全绿，进入正式 review。
