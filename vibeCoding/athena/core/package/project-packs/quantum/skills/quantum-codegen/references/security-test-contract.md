# Security Test Convention Pack Contract

`quantum-codegen` (mode=security) only runs scoped security verification after it has read and validated the target
frontend/backend Convention Packs. The packs are the single source for auth, authorization,
data-scope, input-validation, dependency-audit, runtime-env, and reporting rules.

## Required Inputs

```text
frontend convention pack:
  conventions.md
  validate.md
  runtime-env.md

backend convention pack:
  conventions.md
  validate.md
  templates/Controller.java.tmpl
  templates/ServiceImpl.java.tmpl
  templates/menu-permission.sql.tmpl
```

## Required Semantics

- Frontend pack must define access guard generation, route-level fallback, mock safety, and a
  runtime-env declaration with `dev_command`, `port`, `health_url`, and `teardown`.
- Backend pack must define `@RequiresPermission`, data-scope read/write checks, SQL/menu permission
  gates, and explicit exemption lines (`data-scope-exempt`) for safe non-data-scope entities.
- Static checks are always allowed inside the current repo scope. Dynamic checks require declared
  runtime-env and authorized test accounts; if either is missing, report blocked instead of
  guessing credentials or endpoints.
- Security evidence must be scoped to changed modules and redact tokens, passwords, cookies, and
  personally sensitive fields.

## Verification Flow

1. Run `python3 scripts/check_security_e2e_pack.py --frontend-pack <fe-pack> --backend-pack <be-pack> --profile security`.
2. Read frontend and backend security gates from `validate.md`.
3. Build the static checklist: permissions, data-scope, input validation, sensitive output, hardcoded
   secrets, dangerous logging, SQL/shell concatenation, and dependency-audit command if declared.
4. Run static checks first; dynamic auth/authz/data-scope/input cases only after runtime-env and
   test accounts are declared.
5. Record command, target scope, expected result, actual result, evidence path, fix, and rerun result.

## Blocking Conditions

- Missing Convention Pack or required security gates.
- Missing runtime-env for a dynamic security test.
- No declared authorized test accounts for role/data-scope cases.
- Any high-risk issue remains open without user-approved waiver.
- A claimed exemption lacks `data-scope-exempt` or `access-guard-exempt` evidence.
