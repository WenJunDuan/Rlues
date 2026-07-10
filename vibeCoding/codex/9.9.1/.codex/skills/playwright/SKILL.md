---
name: playwright
description: |
  Playwright browser/E2E testing workflow for runtime verification. Use when Codex needs to add, run, debug, or document frontend/browser tests, smoke-test a dev server, verify UI flows during athena-runtime-verify, capture traces/screenshots, or turn manual browser checks into repeatable tests.
---

# /playwright — Browser Runtime Tests

## Core Rule

Use Playwright when the acceptance signal depends on a real browser: routing, forms, auth flows, rendering, navigation, API-backed UI state, responsive layouts, downloads/uploads, or regressions that unit tests cannot see.

For Athena v9.8.0, this skill is the frontend/E2E test arm of `athena-runtime-verify`. It should produce evidence that can be pasted into `sprints/{slug}/runtime-verify.md` under `## 测试场景 (实跑)`.

Official references:
- Playwright intro: https://playwright.dev/docs/intro
- Writing tests: https://playwright.dev/docs/writing-tests
- CLI: https://playwright.dev/docs/test-cli
- Codegen: https://playwright.dev/docs/codegen
- Trace viewer: https://playwright.dev/docs/trace-viewer

## Workflow

1. Detect project setup before adding anything:
   - Existing Playwright: inspect `playwright.config.*`, `tests/`, `e2e/`, `package.json` scripts.
   - No Playwright: prefer adding `@playwright/test` and a minimal config/test file that fits the repo.
   - If the repo already uses Cypress/Vitest browser mode/etc., avoid wholesale migration; add Playwright only if runtime verification needs real browser coverage.

2. Start or reuse a deterministic app target:
   - Prefer an existing dev/preview script from `package.json`.
   - Use a fixed port when possible.
   - Set `baseURL` in config or pass it via `PLAYWRIGHT_BASE_URL`.
   - Do not leave background servers running at the end of the task.

3. Write tests through user-visible behavior:
   - Use role/text/test-id locators instead of brittle CSS/XPath.
   - Use Playwright web-first assertions such as `await expect(locator).toBeVisible()`.
   - Keep tests small: one critical flow or acceptance behavior per test.
   - Cover at least normal, boundary, and failure/empty states when doing `runtime-verify`.

4. Run and iterate:
   - Main path: `npx playwright test`.
   - Debug path: `npx playwright test --headed`, `npx playwright test --ui`, or `npx playwright codegen <url>` when exploring selectors.
   - Trace path: `npx playwright test --trace on` then inspect with `npx playwright show-trace <trace.zip>`.
   - If browser binaries are missing, run `npx playwright install` or the narrower browser install requested by the repo.

5. Record evidence:
   - Include exact command, exit code, and the important pass/fail output.
   - For `athena-runtime-verify`, write a row in `runtime-verify.md` with scenario, type, command, actual output, and verdict.
   - If a test first fails and then passes after a fix, record both the failing symptom and the passing rerun.

## Athena Integration

- `Feature`: use when UI/API behavior is risky or user-visible.
- `Refactor/System`: use for browser-facing flows before review; this is part of runtime verification.
- `Bugfix`: use when the bug is reproducible in the browser, even though full runtime-verify is usually skipped.
- `Hotfix/Quick`: run only the smallest smoke path needed.

## Resources

Read `references/runtime-patterns.md` when you need concrete command patterns, config snippets, or evidence table examples.
