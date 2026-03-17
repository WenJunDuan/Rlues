---
name: e2e-testing
description: E2E 测试 — T 阶段可选使用 (Web 项目)
context: main
---
## 管道位置: T (verification之后, 可选)

## 触发条件
项目有 playwright/cypress/selenium 依赖

## 步骤
1. 检测 E2E 框架
2. 运行现有 E2E 测试
3. 如果是新功能且有 UI → 建议写 E2E 测试覆盖关键用户流程
4. 结果追加到 quality.md
