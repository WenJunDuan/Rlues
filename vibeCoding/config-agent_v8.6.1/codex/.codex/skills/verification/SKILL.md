---
name: verification
description: 分级验证清单
context: main
---
Path A (基础): `npm test` 通过 + 手动确认
Path B (标准): 单测 + `tsc --noEmit` + `eslint` + `npm audit`
Path C+ (严格): 标准 + E2E (e2e-runner) + 安全审计 (security-auditor) + 性能基线
验证失败 → 读 `skills/debugging/SKILL.md` 进入调试循环
