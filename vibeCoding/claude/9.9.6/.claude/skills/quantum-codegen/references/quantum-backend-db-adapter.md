# quantum-backend DB Adapter

Use this reference when `scaffold_id=quantum-backend` or the target Convention Pack path ends with
`quantum-backend/docs/ai/convention-pack`.

## Pack Location

```text
<quantum-backend-root>/docs/ai/convention-pack
```

Resolve the root from the user target or current workspace; never hard-code a home directory.

The pack is read-only input for this skill. Project-specific edits belong in `quantum-backend`;
skill logic belongs in the Rlues package.

## DB Rules

- Dialect is PostgreSQL, derived from `deploy/init.sql`; do not generate MySQL syntax.
- Design document path: `docs/db/{module}-schema-design.md`.
- DDL path: `deploy/sql/{module}-ddl.sql`.
- Table names and columns use lowercase snake_case.
- Standard business tables include `id`, `create_time`, `create_by`, `update_time`, `update_by`,
  `deleted`, and `version`.
- `dept_id` is required when records have department ownership; unclear ownership defaults to
  requiring `dept_id`.
- Global config/dictionary and many-to-many relation tables need explicit exemption reasoning.

## G5 Gate

Run and report the G5 checks from `validate.md`:

- G5a paired design document and DDL exist.
- G5b design and DDL cross-reference each other.
- G5c no `{{...}}` placeholders remain.
- G5d DDL columns appear in the design document.
- G5e data-scope ownership is filled and not TODO.

Missing G5 evidence means schema generation is incomplete.
