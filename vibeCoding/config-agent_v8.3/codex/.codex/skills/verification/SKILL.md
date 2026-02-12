---
name: verification
description: V 阶段分级清单 — Path 决定验证严格度和失败升级链
context: main
---

# Verification — Path 分级清单

## SP verification 自动处理基础检查。本 skill 只添加:

### 分级清单

| Path | 检查项 |
|:---|:---|
| A | `npm test` 通过即可 |
| B | + `npx eslint .` clean + `npx tsc --noEmit` |
| C | + 覆盖率 ≥ 80% + 无 TODO/FIXME + 无 console.log |
| D | + 集成测试 + 性能基线 + `npm audit` 安全扫描 |

### 失败升级链

```
失败 → 自动修复重试 (max 3)
  → 仍失败 → SP debugging 自动触发
    → 仍失败 → cunzhi: 请求人工介入
```

### .ai_state 记录

每次 V 阶段写入 `verified.md`:
```markdown
## 验证 {日期}
- Path: {当前 Path}
- 通过: {列表}
- 失败: {列表 + 原因}
- 修复: {如有}
```
