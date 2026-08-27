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

> ⚙ **机器契约** — 这里仅定义可观测的验收条目; 解析与门禁实现不在模板重复。
>
> 1. 每条 AC 都是可观测结果，使用列表项表达，避免占位语句。
> 2. 条目正文只描述本条目标，不引用其他 AC 编号或内部实现细节。
> 3. `review-manifest.yaml` 仅在显式存在时启用逐 AC 证据绑定；不存在时不启动绑定链。
> 4. 需要绑定时，在证据文件中给出命令、产物或最终 review 的可复核出处。
> 5. 变更门禁规则时改实现与参考文档，不在每个 sprint 模板复制规则。

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

派生 `review-packet.md`（hash + AC 全集，≤80 行）。作者不自审。R/S 或用户显式要求时由非作者会话执行 packet。
