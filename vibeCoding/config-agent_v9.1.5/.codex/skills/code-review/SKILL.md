---
name: code-review
description: 代码审查 — 配合 /review 原生审查 (NeoLabHQ code-review 模式)
context: main
---
## 审查维度
1. 逻辑正确性: 边界条件、错误处理、并发安全
2. 可读性: 命名清晰、职责单一、注释 WHY 不 WHAT
3. 性能: N+1 查询、不必要循环、内存泄漏
4. 安全: 注入、硬编码密钥、未验证输入
5. 测试质量: 有意义, 不只刷覆盖率

## 工具: `/review` 原生代码审查
## 格式: `{文件}:{行号} | {MUST-FIX|SHOULD-FIX|NIT} | {描述} | {建议}`
## 无问题: "APPROVED — 无需修改"
