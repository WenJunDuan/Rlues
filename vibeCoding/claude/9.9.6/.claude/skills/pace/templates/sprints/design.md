---
sprint_slug: ""                # YYYY-MM-DD-{slug}
path: ""                       # PACE 路径: Feature | Refactor | System | ...
created: ""
last_updated: ""
---

# Design — {sprint_slug}

## 背景 (context)

[一段话: 为什么要做这个改动, 业务/技术驱动]

## 目标 (goals)

- 主要目标: ...
- 次要目标: ...

## 非目标 (non-goals)

- 本次不做: ...

## 关键决策 (key decisions)

[design 阶段拍板的技术选型, ship 后应沉淀为 compound/decision-*.md]

- 决策 1: ...
- 决策 2: ...

## 验收标准 (acceptance criteria)

> spec-compliance subagent 会逐项对比 git diff. 写清楚.

- [ ] AC1: ...
- [ ] AC2: ...
- [ ] AC3: ...

## 实现要点 (implementation notes)

[本次改动涉及的文件 / 关键算法 / 数据流]

## File Structure Plan

> 列出本次会改/新增的文件, spec-compliance subagent 会检查覆盖

```
src/
├── api/
│   ├── refresh.ts       (新增)
│   └── jwt.ts           (修改)
└── tests/
    └── refresh.test.ts  (新增)
```

## 风险与权衡 (risks & trade-offs)

- 风险 1: ...
- 缓解: ...

## 历史决策对齐 (read compound/decision-*.md)

[plan stage 主 agent 必须读 _index.pointers.latest_decisions, 写在这里说明是否冲突]

---

## Round 1 (initial draft by main agent, ultrathink/xhigh)

[主 agent 第一版 design 内容写在这]

---

## Round 1 · Critic Findings (critic subagent, {timestamp})

> 由 critic subagent 追加. 不要手工修改本段.

### VERDICT: PASS | NEEDS_REVISION

### 评分

| 维度 | 评分 (1-5) | 关键 finding |
|---|---|---|
| 边界条件 | - | - |
| 错误处理 | - | - |
| 测试覆盖 | - | - |
| 历史决策对齐 | - | - |
| 复杂度 | - | - |
| 历史教训 | - | - |

### Findings (按严重度)

#### F1 [P0] (一句话题目)
- 现象: ...
- 建议: ...
- 引用: compound/...md (若有)

### 下一轮重点 (若 NEEDS_REVISION)

[critic 给主 agent 的修订方向]

---

[若 NEEDS_REVISION, 主 agent 在这里追加 Round 2, 再触发 critic, 直到 PASS 或达 plan_critique_max_rounds]
