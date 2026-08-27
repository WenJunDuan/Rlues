# Athena REVIEW.md (stable, review-only)

Do not load sprint narrative. Use the sprint `review-packet.md` plus the diff.

Dimensions (one pass): Spec coverage, Correctness, Security, Test risk, Over-engineering. Refactor/System also Evidence.

Write `reviews/implementation-review.md` with YAML frontmatter:

```yaml
schema_version: 1
mode: implementation
packet_sha256: "<sha256 of review-packet.md>"
reviewed_diff_sha256: "<sha256 of source diff excluding .ai_state>"
review_run_id: "<unique id>"
native_output_ref: "direct"
verdict: PASS
finding_counts: {P0: 0, P1: 0, P2: 0}
dimensions: [spec, correctness, security, tests, overengineering]
```

Transcription of a native `/code-review` run must set `native_output_ref` to the transcript path and must not change severity. Same-cause P0 twice on targeted re-review → stop and return to the user.

Nit cap: at most 5 P2/INFO.
