---
name: verification
description: 分级验证清单 — T 阶段
---
### Path A
- [ ] 功能正常 + lint 无新错

### Path B
- [ ] + 单测通过 + 类型检查 + plan.md 全 DONE

### Path C+
- [ ] + E2E + 安全审查 + 无硬编码密钥

输出 .ai_state/verified.md。Path A 不检查 plan.md。
