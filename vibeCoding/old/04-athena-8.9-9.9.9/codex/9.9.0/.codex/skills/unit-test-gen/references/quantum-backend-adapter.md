# quantum-backend Test Adapter

Use this reference when `scaffold_id=quantum-backend` or the target Convention Pack path ends with
`quantum-backend/docs/ai/convention-pack`.

## Pack Location

```text
/Users/mi_manchi/workspace/quantum/quantum-backend/docs/ai/convention-pack
```

The pack is read-only input for this skill. Project-specific edits belong in `quantum-backend`;
skill logic belongs in the Rlues package.

## Test Stack

- Service tests: JUnit5 + Mockito + AssertJ, no Spring container.
- Controller tests: MockMvc standalone setup with manual dependency injection.
- DTO validation tests: direct Jakarta Validator construction.
- Contract tests: reflection over controller signatures and annotations.
- Maven command shape: `mvn -pl <module> test`, with `-am` when reactor dependencies changed.

## Required Coverage

Generated tests must cover:

- data-scope read rejection,
- data-scope write rejection,
- write endpoint permission-code contracts,
- page-query validation annotations,
- optimistic-lock conflict behavior.

Run and report the G6 checks from `validate.md`. Missing G6 evidence means test generation is
incomplete.
