# Harness Iteration v1.1

distribution: package-root-only

This document is a distributable release artifact. It is not installed as an Athena skill and does not change the built-in skill count.

## Dogfood by release size

- Patch: targeted smoke and regression evidence is sufficient.
- Minor: validate in at least one real project.
- Major: validate in real projects for at least two weeks.

## Iteration depth by change size

- Changes touching at most five files may keep challenge and rebuttal evidence in one design document.
- Structural changes use the full four-round iteration record.
- Every Round 1 proposal must retain at least one non-empty rebuttal; percentage shrinkage is guidance, not a gate.

## Forward-looking integrations

Officially announced or beta capabilities may be integrated behind a default-off flag with fail-open behavior. Unverified APIs must not be encoded.

## Source policy

Authority-source fetch failures stop the related conclusion; do not invent evidence. Local repository checks use `~/workspace/Rlues` directly.
