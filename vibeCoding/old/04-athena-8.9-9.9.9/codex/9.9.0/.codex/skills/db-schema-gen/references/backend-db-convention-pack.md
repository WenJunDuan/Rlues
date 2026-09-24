# Backend DB Convention Pack Contract

`db-schema-gen` only writes database design or DDL artifacts after it has read and validated the
target backend Convention Pack. The pack is the single source for dialect, migration layout,
table-design documentation, DDL syntax, data-scope defaults, and validation gates.

## Required Structure

```text
docs/ai/convention-pack/
  conventions.md
  db-conventions.md
  validate.md
  templates/
    ddl.sql.tmpl
    schema-design.md.tmpl
```

## Required Semantics

- `db-conventions.md` must define database dialect, table/column naming, audit columns, optimistic
  lock column, logical delete column, data-scope ownership, sensitive field notes, and forbidden
  shortcuts.
- `validate.md` must define G5 gates for paired schema-design and DDL artifacts.
- `schema-design.md.tmpl` and `ddl.sql.tmpl` must preserve `{{module}}`, `{{Entity}}`, and
  `{{table}}` placeholders until the generator instantiates them.
- The generated schema-design document and DDL must cross-reference each other and be changed in
  the same delivery.

## Generation Flow

1. Run `python3 scripts/check_backend_pack.py <pack-dir> --profile db`.
2. Read `db-conventions.md`, `validate.md`, and the two DB templates.
3. Map requirement fields to table names, columns, indexes, audit/version/deleted fields, and
   data-scope classification before writing files.
4. Generate the semantic design document and executable DDL as separate artifacts.
5. Run the G5 checks from `validate.md`; repair drift before reporting completion.
6. Record changed files, G5 results, and any data-scope exemption line.

## Blocking Conditions

- No Convention Pack or missing required DB files/templates.
- No explicit database dialect.
- No paired schema-design and DDL output plan.
- Data-scope ownership unclear and no documented safe default.
- Validation commands unavailable or failing.
