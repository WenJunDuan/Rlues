---
sprint_slug: ""                # YYYY-MM-DD-{slug}
path: ""                       # PACE 路径: Feature | Refactor | System | ...
created: ""
last_updated: ""
---

# Design — {sprint_slug}

> 电报体。门禁标题勿改。背景≤5行。AC 一句一条。

## 背景 (context)

[为什么做。业务/技术驱动各一句]

## 目标 (goals)

- 主要目标: ...
- 次要目标: ...

## 非目标 (non-goals)

- 本次不做: ...

## 关键决策 (key decisions)

[design 阶段拍板的技术选型, ship 后应沉淀为 compound/decision-*.md]

- 决策 1: ...
- 决策 2: ...

## Done Contract

> 机器契约: AC 可观测, 禁占位; 不交叉引用 AC 编号; 本段唯一验收; 证据给出处; 门禁规则不写进本模板。 review-manifest 存在时保留其绑定校验。

- [ ] AC1: ...
- [ ] AC2: ...
- [ ] AC3: ...

## 实现要点 (implementation notes)

[本次改动涉及的文件 / 关键算法 / 数据流]

## File Structure Plan

> 列出本次会改/新增的文件; 一轮 review 的 Spec coverage 维对照此图

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

并行派工、恢复、审查输入绑定与真实全栈准入按 `~/.agents/skills/pace/references/execution-contracts.md`；只加入本 sprint 适用输入，不复制整份协议。

派生 `review-packet.md`（hash + AC 全集，≤80 行）。作者不自审。R/S 或用户显式要求时由非作者会话执行 packet。
