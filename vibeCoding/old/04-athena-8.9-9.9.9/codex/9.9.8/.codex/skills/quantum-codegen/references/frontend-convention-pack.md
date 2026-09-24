# Frontend Convention Pack Contract

`quantum-codegen` (mode=page) only writes into a frontend project after it has read and validated that
project's Convention Pack. The pack is the single source for framework, routing, component,
permission, mock, and validation rules.

## Required Structure

```text
docs/ai/convention-pack/
  conventions.md
  runtime-env.md
  validate.md
  templates/
    access.ts.tmpl
    api.ts.tmpl
    index.tsx.tmpl
    mock.ts.tmpl
    model.ts.tmpl
    route-registration.md
    search-schema.ts.tmpl
```

## Required Semantics

- `conventions.md` must define module layout, naming, route registration, API/data access,
  permission guard, mock/demo, table/form, and error-state rules.
- `validate.md` must define typecheck/lint/build commands and security gates. Gates must check
  evidence, not just success strings.
- `runtime-env.md` must define `dev_command`, `port`, `health_url`, and `teardown` for local demo
  verification.
- Templates must preserve placeholders for `{{Entity}}`, `{{entity}}`, and route/module fields
  until the generator instantiates them.
- Runtime commands, ports, health URLs, and teardown must come from `runtime-env.md`; do not infer
  them from package scripts.

## Generation Flow

1. Run `python3 scripts/check_frontend_pack.py <pack-dir>`.
2. Read `conventions.md`, `validate.md`, and only the templates needed for the requested page type.
3. Map requirement fields to page files, API contract, mock schema, search schema, and permission
   actions before writing files.
4. Write files by following templates first, then fill business-specific fields.
5. Run validation commands from `validate.md`; repair failures before reporting completion.
6. Record changed files, commands, security gates, route registration, and runtime evidence.

## Blocking Conditions

- No Convention Pack or missing required files.
- No frozen API contract/mock schema.
- No permission/access rule and no explicit exemption line.
- No runtime-env for demo verification when the task asks for a runnable demo.
- Validation commands unavailable or failing.
