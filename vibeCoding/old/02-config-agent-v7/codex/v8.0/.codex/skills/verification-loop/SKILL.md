---
name: verification-loop
description: |
  Verify-fix-retry loop with cross-model validation support.
  v8.0: Added --cross mode for dual-model verification.
---

# Verification Loop Skill

## 标准验证

```
Execute → Verify → Pass? ──→ Done
                    │ No
              Analyze → Fix → Retry (max 3)
                               │ Fail x3
                         cunzhi: 人工介入
```

## 验证方法 (按优先级)

1. 运行现有测试套件
2. TypeScript 类型检查 (`tsc --noEmit`)
3. Lint 检查
4. 手动逻辑验证 (读代码)

## 交叉验证 (--cross)

```
Model A 实现代码
  → Model B 审查代码 (不同视角)
  → 差异报告
  → 综合修复
```

交叉验证适用于 Path C/D 的关键功能。

## 失败处理

| 失败次数 | 动作 |
|:---|:---|
| 1 | 分析原因，修复，重试 |
| 2 | 换方法/换策略，重试 |
| 3 | cunzhi 请求人工介入 |

所有失败和修复记录写入 `.ai_state/doing.md` 的当前任务注释。
