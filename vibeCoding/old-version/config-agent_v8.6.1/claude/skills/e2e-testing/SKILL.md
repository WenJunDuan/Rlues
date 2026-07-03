---
name: e2e-testing
description: Playwright E2E 端到端测试 (源自 ECC e2e-runner)
context: main
---
Path C+ 的 T 阶段:
1. 检查 `playwright.config.ts` 存在
2. 不存在 → `npx playwright install && npx playwright init`
3. 调用 e2e-runner 子代理执行测试
4. 失败 → 截图 + 结构化报告 → 交回 builder 修复
5. 关键页面: 首页、登录、核心功能流程
