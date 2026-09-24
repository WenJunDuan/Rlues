---
name: pace
description: PACE 路由与 4 核心 + 5 条件 stage 全景。面包屑失效或需全景时 Read。
---

# PACE — Router & State Machine (v9.9.9)

新任务先按 [athena-dev](../athena-dev/SKILL.md) 分诊, 再按影响选路径。旧 stage/next_action 不定新任务级别。明确后立刻做已授权工作。

## 6 路径

| 路径 | 触发 | stage | review | polish | worktree |
|---|---|---|---|---|---|
| **Hotfix** | 显式指定, 或紧急有界恢复 | impl → ship | 风险触发 | ❌ | ❌ |
| **Bugfix** | 已知缺陷局部修 | report → impl → review → ship | ✅ 一次 | ❌ | ❌ fix-note |
| **Quick** | 只读诊断, 或≤3文件小改 | 只读 plan→ship; 修改 plan→impl→[review?]→ship | 只读不套实现审查 | ❌ | ❌ |
| **Feature** | 新功能, 单模块 | plan → impl → [runtime-verify?] → review → ship | ✅ 一次 | ❌ | 可选 |
| **Refactor** | 改架构, ≥5 文件 | plan → impl → runtime-verify → polish → review → ship | ✅ 一次 | ✅ | ✅ |
| **System** | 跨模块 | plan → design → impl → runtime-verify → polish → review → ship | ✅ 一次 | ✅ | ✅ |

```
[brainstorm] → [roadmap] → plan → [design] → impl → [runtime-verify] → [polish] → review → ship
```

作者不自审。R/S 才独立挑战 packet。义务全文 [stages.md](references/stages.md)。

## 路由

判据只见 [athena-dev](../athena-dev/SKILL.md)。普通结论: `_index.route_history` 一行 + `route_confidence`。真 re-route 才写 route-note。
写不出可观察目标才 brainstorm。诊断目标清、根因未知 ≠ 需求模糊。

护栏是地板: ≥2 独立可验收切片 → roadmap; 跨模块/≥5 文件 → Refactor; 显式 Hotfix → 直接 impl, 优先于文件数。只许加码, 不许低于地板。

同任务 re-route 只升不降。独立插入按 [切换合同](../athena-dev/references/playbook.md)。
- 机械: Quick>3 / Feature>10 文件 → `next_action=re-route`
- 语义: checklist 膨胀>50% / 跨模块 / 关键假设推翻
- 动作: 补新路径欠的 stage
- 降级仅用户明示

写入: 绿=主 thread; 黄=`spawn_agent`; 红=主 thread 建绝对 worktree, agent 首条 `pwd` + 每次 `workdir`。细节 stages.md impl。
writer 每次派发串行完成 [真实 ID 握手](references/orchestration.md#spawn-binding-handshake)。agent 每任务最多 70 轮, 到限返回进度; CX 为指令约束, 非原生硬限。

## References（按需 Read）

| 场景 | Read |
|---|---|
| stage 义务 | `references/stages.md` |
| impl-entry / writer / review / ship 字段 | [门禁速查](references/gate-contracts.md) |
| 编排 / worktree / 握手 | `references/orchestration.md` |
| hook / 例外 | `references/hooks.md` |
| 插件 | `references/plugins.md` |
| MCP | `references/mcp.md` |

## 最小循环

- plan/design: Feature+ 写 design.md + 派生 packet; 只读Quick 最短 session-log; Hotfix 可省设计
- impl-entry: Feature+ 先验 AC + packet hash/AC 双射（≤80 行）
- impl: 红黄绿区; generator 不预加载本 skill
- runtime-verify / polish: R/S 强制; polish 在 review 前
- review: 一次; 真异步才 `await-review-result`
- ship: gate 认 frontmatter + hash

恢复 [state-contract.md](references/state-contract.md); 派发/接收 [execution-contracts.md](references/execution-contracts.md); 全栈 [fullstack-contract.md](references/fullstack-contract.md); 平台 [platform-contracts.md](references/platform-contracts.md)。
