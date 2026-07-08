# E2E Convention Pack Contract

`playwright-e2e` writes repeatable browser tests only after it has read and validated the target
Convention Pack and runtime-env. It wraps the existing `playwright` skill for browser mechanics; it
adds PACE delivery rules, evidence capture, and fail-closed environment orchestration.

## Required Inputs

```text
frontend convention pack:
  conventions.md
  validate.md
  runtime-env.md

backend convention pack:
  conventions.md
  validate.md
```

## Required Semantics

- `runtime-env.md` must declare `dev_command`, `port`, `health_url`, and `teardown` at minimum for
  frontend demo mode. Full-stack mode must also declare backend/database commands or mark them
  external with health and cleanup boundaries.
- Frontend conventions must define route registration, API client usage, permission guards, mock
  switch rules, and reportable validation gates.
- Backend conventions must define menu/component alignment and security gates so E2E tests can map
  visible pages to real permission codes.
- Playwright traces, screenshots, videos, and HTML reports are evidence artifacts, not optional
  decorations. Record paths in `runtime-verify.md` or the delivery report.

## Generation Flow

1. Run `python3 scripts/check_security_e2e_pack.py --frontend-pack <fe-pack> --backend-pack <be-pack> --profile e2e`.
2. Read requirements, API contracts, route registration, permission matrix, and runtime-env.
3. Start declared environments in dependency order; poll each `health_url`.
4. Use the existing `playwright` skill to write rerunnable tests from acceptance criteria.
5. Run tests, inspect trace/screenshot/report on failure, repair, and rerun.
6. Teardown declared processes/containers/data, then record evidence and uncovered paths.

## Blocking Conditions

- Missing runtime-env or health URL.
- No declared test account/data strategy for authenticated flows.
- Browser test depends on one-time manual clicks instead of a committed/rerunnable test.
- E2E passes only with mock data when the checkpoint requires real backend integration.
- Evidence paths are not recorded for review and delivery reporting.
