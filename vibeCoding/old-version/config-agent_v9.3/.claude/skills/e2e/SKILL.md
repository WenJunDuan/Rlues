---
name: e2e
description: 端到端测试。有 E2E 框架 (Playwright/Cypress) 且 Path C+ 或用户要求时触发。
---
# E2E Testing

## 前置
项目有 E2E 框架 + Path C+ 或用户要求

## 流程
1. 基于 design.md 验收标准编写 E2E 用例
2. `npx playwright test` 或项目命令
3. 失败 → 定位是测试问题还是实现问题
4. 结果追加 quality.md

## 无框架
手动验证清单: 列出关键用户流程 + 验证步骤
