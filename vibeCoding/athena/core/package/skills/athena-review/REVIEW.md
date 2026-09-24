# Athena REVIEW.md (stable, review-only)

Do not load sprint narrative. Use `review-packet.md` + diff.
电报体: findings 骨架句; P2/INFO ≤5。frontmatter 字段名不改。

Dimensions (one pass): Spec coverage, Correctness, Security, Test risk, Over-engineering. Refactor/System also Evidence.

Return the result; the main agent persists `reviews/implementation-review.md` with YAML frontmatter:

```yaml
schema_version: 1
mode: implementation
packet_sha256: "<sha256 of review-packet.md>"
reviewed_diff_sha256: "<sha256 of source diff excluding .ai_state>"
review_run_id: "<unique id>"
native_output_ref: "<actual native output reference>"
verdict: PASS
finding_counts: {P0: 0, P1: 0, P2: 0}
dimensions: [spec, correctness, security, tests, overengineering]
```

Transcription of a native `/code-review` run must set `native_output_ref` to the transcript path and must not change severity. Same-cause P0 twice on targeted re-review → stop and return to the user.

Nit cap: at most 5 P2/INFO.

Dispatch and acceptance follow `skills/pace/references/execution-contracts.md`: persist real target/run and packet/input/evidence bindings, recompute at acceptance, retain stale results as superseded. Do not synthesize missing metadata or claim a missing result passed.
