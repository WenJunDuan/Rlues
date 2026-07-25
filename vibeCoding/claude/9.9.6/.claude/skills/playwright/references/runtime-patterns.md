# Playwright Runtime Patterns

## Install Or Reuse

Prefer the repo's existing scripts. If Playwright is absent and browser verification is required:

```bash
npm i -D @playwright/test
npx playwright install
```

If a repo already has `pnpm`, `yarn`, or `bun`, use that package manager consistently.

## Minimal Config Shape

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

Use `webServer` in config only when it is reliable in the repo. Otherwise start the server explicitly in the task and stop it after tests.

## Test Pattern

```ts
import { test, expect } from '@playwright/test';

test('user can open the dashboard', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
});
```

Prefer `getByRole`, `getByLabel`, `getByText`, and stable `getByTestId`. Avoid CSS selectors unless the UI has no accessible affordance.

## Runtime Verify Evidence Row

```markdown
| 登录成功 | E2E | `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5173 npx playwright test tests/e2e/login.spec.ts --project=chromium` | `1 passed (3.2s)` | PASS |
```

For a repaired failure:

```markdown
| 空列表渲染 | E2E | `npx playwright test tests/e2e/empty-state.spec.ts --project=chromium` | 改前: `Timeout 5000ms waiting for getByText("暂无数据")`; 改后: `1 passed (2.1s)` | PASS(已修) |
```

## Debug Commands

```bash
npx playwright test --headed
npx playwright test --ui
npx playwright codegen http://127.0.0.1:5173
npx playwright test --trace on
npx playwright show-trace test-results/**/trace.zip
```

Only commit traces/screenshots/videos if the repo already tracks such artifacts or the user explicitly asks. Otherwise use them for debugging and keep the durable evidence in `.ai_state`.
