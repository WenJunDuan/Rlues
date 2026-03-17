---
name: tdd
description: 测试驱动开发 — 强制 RED→GREEN→REFACTOR (obra/superpowers 模式)
context: main
---
## 铁律
写功能代码前必须先有失败的测试。PostToolUse hook 会检查。

## 分级
- **L1** (Path A): 关键路径有测试即可
- **L2** (Path B): 严格 RED→GREEN→REFACTOR
- **L3** (Path C+): + E2E, 覆盖率 >80%

## 流程 (L2, 每个 Task)

### 思考
- 要测哪些场景? 正常路径 + 边界条件 + 异常输入
- **动手**: `mcp-deepwiki` 查测试框架/mock 库用法
- 最小实现是什么? 不要提前抽象

### 执行
1. 写失败测试 → 运行确认红色
2. 写最小实现 → 运行确认绿色
3. 重构 → 运行保持绿色
4. `git add . && git commit -m "feat: {Task}"`
5. plan.md: `- [ ]` → `- [x]`
6. doing.md: DOING → DONE

## 违规处理
PostToolUse prompt hook 检测到源码修改但无测试 → 返回 `{ok: false}` → agent 必须补测试

## 测试命令自动检测
package.json → npm test | pyproject.toml → pytest | Cargo.toml → cargo test | go.mod → go test ./...
