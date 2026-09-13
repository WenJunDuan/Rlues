# quantum Security Adapter

Use this reference when `scaffold_id=quantum` or the target packs match the quantum frontend/backend
Convention Pack locations.

## Pack Locations

```text
<quantum-front-root>/docs/ai/convention-pack
<quantum-backend-root>/docs/ai/convention-pack
```

Resolve both roots from the authorized target or current workspace; never assume a username or
fixed workspace prefix.

The packs are read-only inputs for this skill. Project-specific convention edits belong in the
quantum repos; skill logic belongs in the Rlues package.

## Static Security Gates

- Frontend: `validate.md` G1-G6, `access-guard-exempt`, `hasPermission`, route fallback, mock safety,
  and `runtime-env.md` markers.
- Backend: `validate.md` G1-G4 plus G5/G6 context when DB/test generation participated,
  `@RequiresPermission`, `@DataScope`, `assertReadable`, `assertWritable`, `assertInDataScope`,
  `data-scope-exempt`, and `menu-permission.sql` consistency.

## Dynamic Security Rules

- Do not infer accounts, passwords, cookies, or JWTs from local files.
- Do not run against production or shared environments unless the user explicitly authorizes the
  target and account set.
- If only frontend runtime-env exists, complete static security checks and mark dynamic FE/BE cases
  blocked pending backend/database runtime-env and test accounts.
- Record blocked dynamic cases separately from static PASS/FAIL so delivery reports do not imply
  unrun authorization coverage.
