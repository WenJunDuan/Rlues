---
name: compound
description: >
  Sprint 的 Quality Gate 通过后触发。把本 Sprint 学到的提炼为结构化条目追加 lessons.md，供下次 R₀ 读取。
---

# compound — 经验沉淀

Gate PASS 后触发 (或用户显式调用 `$compound`)。

## 输入
- .ai_state/reviews/sprint-N.md (审查报告)
- git diff (本 Sprint 的所有变更)
- .ai_state/tasks.md (完成项)
- .ai_state/design.md (设计 vs 实际实现对比)

## 提炼方法

从以上输入里**找真实发现**，不写仪式性废话。每 Sprint 0-N 条不强制。

- **Pattern**: 什么解法有效且可复用？(带代码行号 / 文件路径)
- **Pitfall**: 什么坑踩过？未来同类场景要提前避开
- **Constraint**: 发现的新约束 (依赖版本、环境、性能边界、API 限制)

没发现可提炼的 → 不写，直接告知用户 "no new lesson"。**不允许编造。**

## 输出

追加到 .ai_state/lessons.md (append-only, 不修改历史):

```markdown
## [YYYY-MM-DD Sprint N] 一句话标题
- **Pattern**: 解法描述 (src/auth.ts:42)
- **Pitfall**: 坑点描述
- **Constraint**: 约束描述
```

已有条目不删不改。append-only 是硬规则。

## 自检

写入后读回验证:
1. 条目有具体的文件/行号/版本引用 (不只是"要注意 X")
2. 一句话标题能让下次 R₀ 快速扫描命中
3. Pattern/Pitfall/Constraint 三段不强制全有，但至少有一段

写完告知用户: "Lessons updated. Next sprint R₀ 会自动读取。"
