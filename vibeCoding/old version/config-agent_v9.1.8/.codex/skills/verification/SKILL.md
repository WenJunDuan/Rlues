---
name: verification
description: 测试运行与验证 — T 阶段
---
## 管道位置: T → 产出 quality.md 验证部分

## 步骤
1. 运行全量测试 → 记录结果
2. 覆盖率 (如可用)
3. Lint / type-check (如可用)

## quality.md 验证部分格式
```markdown
## 验证报告
- 测试: X passed / Y total
- 覆盖率: XX%
- Lint: 0 errors
- Type-check: 0 errors
```
