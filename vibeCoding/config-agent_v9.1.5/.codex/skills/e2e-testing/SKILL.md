---
name: e2e-testing
description: 端到端测试 — Path C/D 的 T 阶段
context: main
---
## 流程
1. 检查 playwright.config.ts 存在
2. `npx playwright test` 执行
3. 收集: 通过率 + 失败详情 + 截图
4. 失败 → 修复 → 重测 (最多 2 轮)
5. 全部通过 → cunzhi [TESTS_PASSED]

## 降级: Playwright 不可用 → 手动功能验证 + 用户确认
