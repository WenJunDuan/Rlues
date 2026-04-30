---
name: compound
effort: xhigh
description: >
  Sprint Gate 通过后触发。两个产物: 1) lessons.md 追加结构化经验 (Pattern/Pitfall/Constraint) 2) sprint-N-summary.md 叙事化简报 (5-8 行). 双输出后自核对避免重复。
---

# /compound — 经验沉淀 (v9.5 双轨)

Gate PASS 后触发 (或用户显式调用)。

## 输入
- .ai_state/reviews/sprint-N.md (审查报告)
- git diff (本 Sprint 所有变更)
- .ai_state/tasks.md (完成项)
- .ai_state/design.md (设计 vs 实际实现对比)
- .ai_state/progress.md (impl 决策日志)

## 双输出

### 输出 1: .ai_state/lessons.md (结构化, append-only)

提炼**真实发现**, 不写仪式性废话。每 Sprint 0-N 条不强制。

- **Pattern**: 什么解法有效且可复用? (带代码行号 / 文件路径)
- **Pitfall**: 什么坑踩过? 未来同类场景要提前避开
- **Constraint**: 发现的新约束 (依赖版本、环境、性能边界、API 限制)

格式见 templates/lessons.md。没发现可提炼的 → 不写。**不允许编造。**

### 输出 2: .ai_state/sprint-N-summary.md (叙事化, 严格 5-8 行)

3 段固定结构 (见 templates/sprint-N-summary.md):
- **做了什么**: 主要交付 + 文件名 (1-2 行)
- **决定了什么**: 关键技术/产品决策 (1-2 行)
- **遗留什么**: 未做完的 task / 已知问题 (1-2 行)

R₀ 阶段下次 sprint **只读最近 2 个 summary**, 旧的不自动加载。

## 自核对 (必做, 写完后立即检查)

1. **重复检查**: lessons.md 新条目和 sprint-summary 内容若 ≥80% 相似 → 改写 summary, 不复述 lessons
2. **长度检查**: sprint-summary 超过 10 行 → 截断或重写更精炼
3. **空内容**: 没有真实发现 → lessons.md 不追加新条目, sprint-summary 仍写但简短 ("Sprint N: 实现了 X, 无新经验")
4. **引用检查**: lessons 条目必须含文件路径或行号; sprint-summary 至少 1 处可验证的事实

不通过 → 重写, 直到通过。

## 与 ~/.codex/lessons/ 的关系

| 文件 | 内容 | 谁写 | R₀ 怎么读 |
|------|------|------|---------|
| `.ai_state/lessons.md` (项目级) | 业务代码 Pattern/Pitfall | compound skill | 全文最近 10 条 |
| `.ai_state/sprint-N-summary.md` (项目级) | 叙事化故事 | compound skill | 最近 2 个 |
| `~/.codex/lessons/INDEX.md` (全局) | 主题索引 | /lesson-curator | 主题命中 |
| `~/.codex/lessons/{date}-{slug}.md` (全局) | 已确认工具链经验 | 用户落档 | 索引命中后 Read |
| `~/.codex/lessons/draft-*.md` (全局) | 自动起草 | lesson-drafter hook | 不读, 待审 |

## 写入完成后

告知用户:
- "Lessons updated: <N> entries" (lessons.md 行数变化)
- "Sprint summary: <一句话总结>" (summary 文件位置)
- "下次 R₀ 阶段会自动读取最近 2 个 summary 和最近 10 条 lessons"
