# Backend Test Convention Pack Contract

`quantum-codegen` (mode=unit) only writes tests after it has read and validated the target backend Convention
Pack. The pack is the single source for test framework, naming, fixture boundaries, required
business-risk coverage, debug loop, and report format.

## Required Structure

```text
docs/ai/convention-pack/
  conventions.md
  test-conventions.md
  validate.md
  templates/
    test-report.md.tmpl
```

## Required Semantics

- `test-conventions.md` must define service, controller, DTO, and contract test shapes.
- It must define the required generated test method names for data-scope read/write, permission
  code, page-query validation, and optimistic-lock conflict coverage.
- `validate.md` must define G6 gates for generated test coverage.
- `test-report.md.tmpl` must preserve report placeholders and include debug-loop rounds.

## Generation Flow

1. Run `python3 scripts/check_backend_pack.py <pack-dir> --profile test`.
2. Read `test-conventions.md`, `validate.md`, and `templates/test-report.md.tmpl`.
3. Map acceptance criteria to required service/controller/DTO/contract tests before writing files.
4. Generate tests first, then repair implementation or fixtures only when the failing test reveals
   a real business gap.
5. Run declared Maven test commands and iterate through the debug loop.
6. Record G6 results, test count, failures, fixes, and residual risks in the report template.

## Blocking Conditions

- No Convention Pack or missing test convention/report template.
- No declared test command.
- Required G6 method names are absent.
- Data-scope exemption is claimed without a positive exemption test and report note.
- Tests pass only by deleting assertions or over-mocking the risk under test.
