---
name: tdd
description: 测试驱动开发 — 强制 RED→GREEN→REFACTOR (obra/superpowers 模式)
context: main
---
## 铁律: 功能代码前必须有失败测试。违反时立即停下补测试。

## 分级: L1(A) 关键路径 | L2(B) 严格TDD | L3(C+) +E2E >80%

## 流程 (L2, 每个 Task)

### 思考
- 测什么场景? 正常 + 边界 + 异常
- **动手**: `mcp-deepwiki` 查测试框架/mock 用法
- 最小实现? 不提前抽象

### 执行
1. 写失败测试 → 运行 → 确认红色
2. 写最小实现 → 运行 → 确认绿色
3. 重构 → 保持绿色
4. `git add . && git commit -m "feat: {Task}"`
5. plan.md 勾选 → doing.md 移到 DONE

## 测试命令
package.json → npm test | pyproject.toml → pytest | Cargo.toml → cargo test | go.mod → go test ./...
