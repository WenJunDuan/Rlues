# quantum E2E Adapter

Use this reference when `scaffold_id=quantum` or target packs match the quantum frontend/backend
Convention Pack locations.

## Pack Locations

```text
/Users/mi_manchi/workspace/quantum/quantum-front/docs/ai/convention-pack
/Users/mi_manchi/workspace/quantum/quantum-backend/docs/ai/convention-pack
```

## Current Runtime Shape

- Frontend demo runtime is declared by `quantum-front/docs/ai/convention-pack/runtime-env.md`.
- Backend/database runtime may be absent in the Convention Pack. If absent, do not infer commands
  from Maven or application files for dynamic full-stack E2E; report full-stack E2E blocked pending
  backend/database runtime-env.
- FE-only mock/demo E2E is allowed only when the checkpoint asks for demo verification. Mark it as
  mock/demo evidence, not real integration evidence.

## E2E Coverage Targets

- Route registration: `backendComponent` and `fullPath` match backend `menu-permission.sql`.
- Auth redirect: unauthenticated access goes to sign-in or denied route according to project rules.
- Permission view: buttons/row actions respect `<entity>-management-access.ts`.
- CRUD happy path and validation path use `apiClient`, URL search state, and declared mock/real mode.
- Evidence includes command, base URL, test file path, screenshot/trace/report path, and teardown.

Missing backend runtime-env or test accounts should block only the dynamic full-stack slice; the
skill can still generate rerunnable tests and static coverage notes from contracts.
