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

> ⚙ **机器契约 (delivery-gate 同步)** — 下面五条是 gate 的机械判据, 不是风格建议。违反即 block。
> 改本节骨架前先读完; **gate 判据变更时须同步更新本块**。
>
> 1. **标题** 只认 `## Acceptance Criteria` / `## 验收标准` (2-3 级), 序号前缀只允许 ASCII `1.` `1)`;
>    CJK 序数 (`## 六、验收标准`) 不匹配 → 解析结果 0 条 → 全部实现写入被拦 (`ACCEPTANCE_HEAD`)。
> 2. **只收列表项** (`-` / `*` / `1.` / `[ ]`); **markdown 表格行一条都不算**; 占位符与泛化陈述
>    (TODO/TBD/待定/"功能正常"…) 被剔除 (`acceptanceCriteria`, `isPlaceholderCriterion`)。
> 3. **编号 11/12 是 harness 保留元标号**: 业务 AC **一律避开**, 从 AC13 起编。占用即*静默免检* ——
>    `validateAcMapping` 排除这两个标号, 而 `validateMetaAcceptance` 会据标号施加另一套无关义务。
> 4. **条目正文内禁写其他 AC 编号**: 标号抽取扫的是条目正文, 判据为
>    `(?:^|[^A-Za-z0-9])(AC\d+)(?![0-9])` (前有非字母数字边界、后不接数字)。在 AC17 正文写
>    "(原 AC11)" 会把保留标号重新注射进标号集。编号映射只写在本节表头注里。
> 5. **每条业务 ACn 需 admissible 证据绑定** (`evidence.yaml` 的 `ac_id` / `covers`, `validateAcMapping`),
>    三形态: `source: command` (带 output_artifact + sha256 + exit 0 + implementation_commit) /
>    `source: artifact` / `source: review` (最低成本, 指向逐 AC SATISFIED 且 VERDICT PASS 的最新 passN)。
>    ⚠ **hook 自动采集的记录不含这两个字段, 不构成绑定**; `tdd-evidence.yaml` 走另一条校验, 也不算。
>    **分级**: 仅在 `review-manifest.yaml` 存在时执行 → Refactor/System 必踩, 其余路径不带 manifest
>    时业务 AC 完全不绑定。义务细节见 `pace/references/stages.md` ship 段。
>
> 写清楚、可观测、附核验命令口径 (spec-compliance 会逐项对比 git diff)。— 同步自 delivery-gate @2026-07-28

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

## Round 1 · critic 轮次 (scaffold — 由 critic subagent 覆写本段头)

<!-- ⚙ 机器契约: critic 轮次由 validateCriticRounds 按 design.md 里字面串
     "Critic" + 空格 + "Findings" 的【全文出现次数】计数 (无位置约束),
     Refactor/System 地板 2, 其余 1。
     critic subagent 追加轮次时, 段头必须逐字写成:
         "## Round N · Critic" + 空格 + "Findings (critic subagent, {timestamp})"
     本模板【刻意不写出该字面串的连续形式】—— 否则每个由本模板实例化的 sprint
     都会起算 1 轮, 使 Refactor/System 的地板 2 实际只强制 1 轮真实审议
     (2026-07-28 实测: 四份模板均自带该幻影轮次)。
     同理, 正文【讨论】该契约时也必须转写, 否则虚增计数。 -->

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
