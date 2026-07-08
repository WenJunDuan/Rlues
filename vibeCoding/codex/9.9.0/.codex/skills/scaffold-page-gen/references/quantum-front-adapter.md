# quantum-front Adapter

Use this reference when `scaffold_id=quantum-front` or the target Convention Pack path ends with
`quantum-front/docs/ai/convention-pack`.

## Pack Location

Default local path:

```text
/Users/mi_manchi/workspace/quantum/quantum-front/docs/ai/convention-pack
```

The pack is read-only input for this skill. Project-specific edits belong in `quantum-front`; skill
logic belongs in the Rlues package.

## Stack

- React 19 + Vite + TypeScript strict.
- TanStack Router, Query, and Table.
- zod v4, zustand, shadcn/Radix, lucide-react.
- Package manager/test runner: `bun`.

## Page Structure

Standard management page modules live at:

```text
src/features/<module>/<entity>/
```

Expected files include `index.tsx`, `api.ts`, `model.ts`, `search-schema.ts`,
`<entity>-management-access.ts`, `mock.ts`, data constants, and component files for provider,
dialogs, table, columns, primary buttons, row actions, bulk actions, action form, delete dialogs,
and optional guards.

## Route Registration

Do not create a new route file. quantum-front uses one dynamic authenticated route. Register the
page in `src/app/navigation/page-registry.tsx`:

- Import `XxxManagementPage` from `@/features/<module>/<entity>`.
- Add `backendComponent: '<module>/<entity>/index'`.
- Add `fullPath: '/<module>/<entity>'`.

The `backendComponent` value must match the backend `sys_menu.component` field exactly.

## API And Data Rules

- Use `apiClient` from `@/lib/http`; do not create a new axios instance or use bare `fetch`.
- Success follows HTTP status; do not branch on `body.code`.
- Normalize backend `unknown` data before returning typed frontend models.
- Long IDs must use `toId` / `toIdList`; never use `Number(record.id)`.
- List queries return `PagedResult<T>` with `pageNum/pageSize/total/pages/records`.
- React Query keys use `['<module>', '<entityPlural>', '<action>', ...]`.
- Mutations use `handleServerError` and precise `invalidateQueries`.

## Permission And Safety Gates

Every generated management page must generate and consume `<entity>-management-access.ts`, unless
the generation report contains:

```text
access-guard-exempt: <Entity> <reason>
```

Run and report the pack gates G1-G6 from `validate.md`, including access guard existence/use,
placeholder cleanup, mock switch not enabled in committed env files, mock type import, and page
registry entry.

## Validation Commands

Use the commands from `validate.md`:

```bash
bunx tsc -b --noEmit
bun run lint
bun run format:check
bun run build
```

Run only the commands appropriate to the current stage, but `build` is the final proof before
claiming a generated page is complete.
