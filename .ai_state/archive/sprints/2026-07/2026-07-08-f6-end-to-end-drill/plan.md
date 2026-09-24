# F6 Plan — end-to-end drill

## Scope

- Audit local `quantum-front`, `quantum-backend`, and `quantum-cowork` repo state.
- Run the full F2-F5 skill regression chain from Rlues.
- Run each quantum repo's feasible local checks without exposing secrets.
- Produce a repeatable drill script that distinguishes static contract readiness from blocked live E2E.

## Acceptance

- Rlues skill regressions pass for scaffold, DB/test, security/E2E, and delivery-loop contracts.
- `quantum-front` runtime-env is present and validated by the scaffold/E2E validators.
- `quantum-backend` MCP manifest and tests pass through Maven reactor.
- `quantum-cowork` MCP provider tests pass locally, with remote freshness recorded.
- If backend runtime-env, live OAuth/test accounts, or remote credentials are absent, dynamic E2E is reported as blocked, not inferred.

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-scaffold-page-gen.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-db-unit-gen.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-security-e2e.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-biz-delivery-loop.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-end-to-end-drill.py`
- `bun test` in `quantum-front`
- `mvn -pl quantum-mcp -am test` in `quantum-backend`
- `bun test` in `quantum-cowork`

## Blocker Policy

Dynamic full-stack E2E requires a backend runtime-env, OAuth/test account path, and a reachable MCP endpoint. Missing any of these becomes a documented dynamic blocker; it does not invalidate the static contract drill.
