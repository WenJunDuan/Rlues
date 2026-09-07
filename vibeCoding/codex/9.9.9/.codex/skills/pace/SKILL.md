---
name: pace
description: PACE 路由与 4 核心 + 5 条件 stage 全景。面包屑失效或需要路由全景时 Read，不必每 sprint 必读。
---

# PACE — Router & State Machine (v9.9.9)

## 6 路径

新的一句话/一段话任务先按 [athena-dev](../athena-dev/SKILL.md) 自动区分只读诊断、修改及旧任务延续，再按实际影响判定路径；旧 stage/next_action 不替新任务定级。明确后立即执行下一项授权工作。

| 路径 | 触发 | stage 流程 | 强制 review? | 强制 polish? | 强制 worktree? |
|---|---|---|---|---|---|
| **Hotfix** | 用户明确指定，或紧急故障的有界恢复 | impl → ship | 风险触发 | ❌ | ❌ |
| **Bugfix** | 已知缺陷的局部修复 | report → (analyze) → impl → review → ship | ✅ 一次 | ❌ | ❌ (fix-note 必写) |
| **Quick** | 只读诊断，或≤3文件小改动 | 只读：plan → ship；修改：plan → impl → [review?] → ship | 用户或风险；只读不套实现审查 | ❌ | ❌ |
| **Feature** | 新功能, 单模块 | plan → impl → [runtime-verify?] → review → ship | ✅ 一次 | ❌ | ❌ (可选) |
| **Refactor** | 改架构, ≥5 文件 | plan → impl → runtime-verify → polish → review → ship | ✅ 一次多维 | ✅ | ✅ 强制 |
| **System** | 跨模块, 系统级 | plan → design → impl → runtime-verify → polish → review → ship | ✅ 一次多维 | ✅ | ✅ 强制 |

## 9 Stage 状态机 (4 核心 + 5 条件)

```
                          (大需求或描述模糊时)
                                ↓
[brainstorm] ──→ [roadmap] ──→ plan ──→ [design] ──→ impl ──→ [runtime-verify] ──→ [polish] ──→ review ──→ ship
                                ↑           (System)              (R/S)            (R/S, 改代码的清理)
                                作者不自审；R/S 才独立挑战 packet
```

## 路由审议 (v9.9.1 · 可审计决策摘要)

路由按任务语义和现场证据判定；判据与新旧任务切换只见 [athena-dev](../athena-dev/SKILL.md)，本页不另定义分诊协议。 普通结论只记 `_index.route_history` 一行 + `route_confidence`；真实 re-route 或重要假设才另立 route-note。

**模糊判定（语义，非字数）**：先结合现有上下文和必要只读检查判断能否写出可观察目标；仍缺决定性信息才澄清/brainstorm。诊断目标明确而根因未知，不算需求模糊。
(废除旧版 `len(input.split()) < 8`: split 按空格切词, 对中文输入恒为 1, 判定失效)

**护栏是地板, 不是天花板** (铁律[分诊]):

| 硬护栏 (不可击穿的下限) | 最低路径 |
|---|---|
| ≥2 个可独立验收交付的切片 | roadmap (hotfix2: 模块数只定风险等级, 不可拆的跨模块不变量单 sprint 做) |
| 跨模块改动 / 预估 ≥5 文件 | Refactor |
| 用户明确指定本次 Hotfix，或紧急故障的有界恢复 | Hotfix 优先于一般文件数路由，直接 impl |

审议只允许在地板之上加码 (Quick 判成 Feature 可以), 不允许低于地板 (System 级判成 Quick 禁止).

## 中途 re-route (只升不降)

只升不降针对同一任务；独立插入任务按 [任务切换合同](../athena-dev/references/playbook.md) 保存旧状态并路由，不继承旧System级别。用户已指定本次Hotfix时不重复询问本次范围降级。

路径不在入口一锤定音. sprint 执行中证据与路径不符 → 重走审议, **只允许升级** (Quick→Feature→Refactor→System):

- **机械触发** (index-updater hook): sprint 改动文件数超路径上限 (Quick>3 / Feature>10) → 写 `next_action=re-route`
- **语义触发** (agent 自查): checklist 膨胀 >50% / 发现跨模块耦合 / design 关键假设被推翻
- **动作**: 重走审议 → route-note 追加 `## Re-route` 段 + `_index.route_history` 记一条 → **补上新路径欠的 stage** (如升 Refactor 需补 runtime-verify + polish + worktree)
- **降级禁止**: 降级 = 给 agent 逃避门禁开合法通道. 确需降级只能用户显式批准

## 写入路由 (铁律[零写入] 红黄绿区)

| 区 | 条件 | 执行者 |
|---|---|---|
| 绿 | ≤3 文件且合计 ≤150 行, 或 Hotfix/Quick/Bugfix | 主 agent 直接做 |
| 黄 | 单模块 Feature | spawn_agent, worktree 可选 |
| 红 | Refactor/System 或并行 ≥2 写者 | 主 thread 建绝对 worktree；任务给路径，agent 首条 pwd |
| 例外 | 改动对象在 repo 外 (安装态 harness 等) | worktree 零隔离效果 → 免 worktree; 设 `_index.harness_target_outside_repo: true`, 改前逐文件备份, 单写者串行 (P9 根治) |

## References (按需 Read, 不要预加载)

| 场景 | Read |
|---|---|
| 进入某 stage 前看详细工作流 / 数据目录 | `references/stages.md` |
| impl-entry / writer 握手 / review / ship 的文件、字段与命令顺序 | [门禁合同速查](references/gate-contracts.md)，正常执行先查；block 或版本不符才回源码 |
| 选编排机制 (subagent / ultracode / /goal / Agent Team) | `references/orchestration.md` |
| 查 hook 联动 / compound 联动 / 项目级例外 | `references/hooks.md` |
| 某 stage 该用哪个插件 / 插件与流程冲突 | `references/plugins.md` (v9.9.0 U6) |
| MCP 连接外部 / MCP 与流程边界 | `references/mcp.md` (v9.9.6) |

## 最小循环提醒

- plan/design: Feature+作者写 `design.md` + 派生 `review-packet.md`；只读Quick仅最短session-log，修改Quick用简短计划，Hotfix可省设计。不spawn critic；R/S或用户要求才由非作者会话挑战packet。
- **spec-gate impl-entry**: Feature+ 进 impl 前先验 design 验收标准 + packet hash/AC 双射（≤80 行）。写不出 AC = 回 plan。
- impl: 按红黄绿区路由写入; generator 不预加载 pace skill
- runtime-verify (R/S 强制): 按 design/runtime-env 实跑；VM 仅在合同要求时必需
- polish (R/S): 会改代码的清理 **在 review 之前**
- review: **一次**独立多维请求（仅实际后台入口异步）；`next_action=await-review-result` 时 Stop 放行；结果 `implementation-review.md`
- ship: gate 认 frontmatter + hash，不数 Critic/passN 标题

恢复与证据：[state-contract.md](references/state-contract.md)；派发/接收/整合：[execution-contracts.md](references/execution-contracts.md)；全栈准入：[fullstack-contract.md](references/fullstack-contract.md)；CX 原生与配置：[platform-contracts.md](references/platform-contracts.md)。


CX writer 每次派发串行完成 [真实 ID 握手](references/orchestration.md#spawn-binding-handshake)。agent 每次任务最多 70 轮，到限返回进度；CX 当前为指令约束，非原生硬限。
