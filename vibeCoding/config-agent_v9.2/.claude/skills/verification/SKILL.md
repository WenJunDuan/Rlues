---
name: verification
description: 测试运行与覆盖率检查 — T 阶段使用
context: main
---
## 管道位置: T → 产出 quality.md (验证部分) → 交给 code-review

## 步骤
1. 运行全量测试 → 记录结果
2. 检查覆盖率 (如可用): 关键路径必须覆盖
3. 运行 lint/type-check (如可用)
4. 写入 .ai_state/quality.md 的验证部分

## quality.md 验证部分格式
```markdown
## 验证报告
- 测试: X passed / Y total
- 覆盖率: XX% (关键路径: 100%)
- Lint: 0 errors
- Type-check: 0 errors
```
