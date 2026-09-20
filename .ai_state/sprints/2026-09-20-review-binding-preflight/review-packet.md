---
source_design_sha256: "0d4c90f8fb0d0ac6cd863d30dc5ad0794b6761bbb6379d7e9c2b440bcb160fe8"
mode: "design"
---

# Review Packet — review binding preflight

## Decision

The review binding CLI must not break its own binding, must say which input drifted with the evidence it actually has, must catch a stale manifest commit at prepare rather than at ship, and must expose the governance hash it already computes instead of forcing operators to reimplement it. Everything still fails closed; only the diagnosis and the timing improve.

## Acceptance mapping

| AC | Roadmap issue | Mechanism | Verification |
|---|---|---|---|
| AC1 | 6 | prepare self-excludes every path the four steps write, from the **stored** `input_paths`; records `excluded_inputs` | session-log / review-doc / `_index.md` declared as inputs; prepare → bind → accept → `validateCurrent` all succeed; empty-after-exclusion fails |
| AC2 | 6 | `input_hashes` persists the whole `inputs` map (declared paths **and** snapshot axes); `evidence_docs`/`evidence_ids` filtered from data already held | only differing entries listed with path and both hashes; aggregate axes name no file; specific doc/id named; pre-`input_hashes` rows degrade explicitly |
| AC3 | 9 | narrow single-field scan of `implementation_commit` vs HEAD at prepare | stale 40-hex fails naming both and which is stale, manifest byte-identical; absent/malformed behaves exactly as today |
| AC4 | 10 | `governance` verb importing the gate's own function **and its `_index.md` resolution rule**, branching before `--run` | equals each gate's computation; correct file chosen from inside a linked worktree; no sprint required; CC/CX outputs diffed equal; writes nothing; missing `_index.md` exits non-zero |
| AC5 | parity invariant | gate diff limited to two export names; Pi `_review-binding.cjs` re-synced | line-by-line diff against `0ca066c`; CX matches CC across AC1-AC4; Pi byte-identical, repairing the missing dedup |

## Challenge points

- The exclusion set is every path the four steps write, not just the session log. `reviews/<mode>-review.md` is the dangerous one: accept writes after its own `assertLive`, so the failure lands at ship via `validateCurrent`, one step later than the bug it replaces. `reviews/_native/*.json` needs no handling because it does not exist at prepare.
- Exclusion must apply to the stored `input_paths`, since `liveInput` re-reads them at every later step. Filtering only the hash input reproduces the bug.
- `excluded_inputs` has no machine consumer today; it is justified because the prepared row is the only record of what was actually bound, and the alternative is a silent hole. AC1 therefore asserts the row content.
- `input_hashes` must persist the snapshot axes too, not just declared paths: the expected values for `design_sha256`/`source_sha256`/`environment_sha256` are otherwise discarded, and AC2's aggregate clause could not name even the axis.
- The governance verb must resolve `_index.md` the way the gate does (`tryRepoRoot` + `findAiState`), not the way every other verb does (`input.context` → worktree root). Measured in this project's worktree the two already diverge, so the CLI-natural choice would print a hash the gate never validates against.
- AC2 promises per-path attribution only where per-path evidence exists. `source_sha256` and `environment_sha256` are aggregate digests and can name an axis, never a file. Promising more than the data supports would be a false claim in an error message.
- Adding `input_hashes` changes a `schema_version: 1` row, so pre-existing rows need a stated degradation rather than a crash.
- The manifest preflight deliberately does not reuse the gate's `parseReviewManifest`: it needs a `pathType` prepare lacks, and it would newly hard-fail manifests that are legitimately incomplete mid-sprint. A narrow single-field scan is not the drift hazard a second full parser would be.
- Prepare-time is the only safe comparison point, and it leaves intact the deliberate tolerance that lets ship bookkeeping commits move HEAD after prepare without voiding a review.
- `accept`'s dedup of reviewer-supplied `Reviewed …` lines is **correct and stays**. It guarantees the gate's exactly-one rule and is regression-tested. An earlier draft of this design wrongly called it a defect; verifying instead of stripping would produce two matches and block ship.
- AC4 requires importing the gate's function rather than reimplementing it; a second implementation is the exact drift the subcommand exists to eliminate. That import forces the only permitted gate edit, which AC5 bounds to two export names.
- Pi's `_review-binding.cjs` is a stale pre-dedup copy that would duplicate binding lines and block ship today. The re-sync is a defect repair, not housekeeping.

## Allowed write set

Only the implementation, tests, three contracts, architecture file and current sprint artifacts listed in the design File Structure Plan. `delivery-gate` logic is excluded; the two `module.exports` names are the sole permitted gate diff.

## Round 2 附录（2026-09-20 ship 期源码面变更）

- 触发: round 1 (run cdfb7313, base baf5d9c) accept 后源码面又变, 门禁按 source_sha256 漂移正确拦截 Stop。
- 待审 delta: `git diff d2f1887..HEAD -- vibeCoding`。仅两类文本变更: ① 99a0be5 还原 stages.md 电报体一节 (3 端, 修正上会话反向同步方向误判); ② ad6ba4d 错字改名「电宝体」→「电报体」(57 文件 63 处, 含「电宝体=电报体」注解与标题收敛)。
- 断言: delta 内 0 个 .cjs/.py 文件; hook 行为面未动; 52/52 测试在当前源码面 PASS (evidence.yaml toolu_014FKwCa 现绑定)。
- 审查焦点: 改名是否破坏任何门禁标题/字段名 (doc-style 明文禁改); 「电宝体=电报体」收敛处语义是否保持; stages.md 还原是否完整忠实于 d556226 引入版。
- Round 1 结论 (PASS, P0=0 P1=0 P2=5) 覆盖 hook 实现本体, 本轮不重审。
