---
name: pace
description: |
  PACE 路由 + 9 stage 状态机. Athena 项目的中枢. 主 agent 进入任何 sprint 前必读.
  v9.7.0: 热路径精简 (铁律[三原语]). 本文件只保留路由判断; stage 详解 / 编排路由表 / hook 联动下沉 references/, 按需 Read.
  v9.9.1: 路由记录候选、证据、权衡、决策与置信度, 不要求暴露私有思维链; 中途 re-route 只升不降.
---

# PACE — Router & State Machine (v9.9.1)

## 6 路径

主 agent 收到用户输入后, 按改动量 + 紧急度判定路径:

| 路径 | 触发 | stage 流程 | 强制 review? | 强制 polish? | 强制 worktree? |
|---|---|---|---|---|---|
| **Hotfix** | 生产事故, 几分钟修 | impl → ship | ❌ | ❌ | ❌ |
| **Bugfix** | 已知 bug, 单文件 | report → (analyze) → impl → review → ship | ✅ 单维 | ❌ | ❌ (fix-note 必写) |
| **Quick** | 小改动, ≤3 文件 | plan → impl → review → ship | ✅ 单维 | ❌ | ❌ |
| **Feature** | 新功能, 单模块 | plan → impl → [runtime-verify?] → review → ship | ✅ 单维 | ❌ | ❌ (可选) |
| **Refactor** | 改架构, ≥5 文件 | plan → impl → runtime-verify → review → polish → ship | ✅ 三维度 | ✅ | ✅ 强制 |
| **System** | 跨模块, 系统级 | plan → design → impl → runtime-verify → review → polish → ship | ✅ 三维度 | ✅ | ✅ 强制 |

## 9 Stage 状态机

```
                          (大需求或描述模糊时)
                                ↓
[brainstorm] ──→ [roadmap] ──→ plan ──→ [design] ──→ impl ──→ [runtime-verify] ──→ review ──→ [polish] ──→ ship
                                ↑           (System)              (3 维度)         (Refactor/System)
                                ultrathink + critic 多轮
```

## 路由审议 (v9.9.1 · 可审计决策摘要)

路由是 triage, 不是查表. 主 agent 收到输入后走 5 步审议 (完整协议 + route-note 格式在 athena-dev):

1. **检查上下文**: 读 `_index.md`、相关 git 状态与用户显式约束
2. **比较候选**: ≥2 个候选路径, 记录支持/反对证据
3. **权衡** (四维): 爆炸半径 (文件/模块数) × 可逆性 × 紧急度 × 需求不确定性
4. **决策 + 置信度**: ≥0.8 直接进; 0.5–0.8 带假设进 (route-note 写明假设 + 廉价退出点); <0.5 停下问用户 1-2 个决定性问题, 或进 brainstorm
5. **落盘摘要**: `sprints/{slug}/route-note.md` + `_index.route_confidence`; 只写结论性证据和权衡, 不写私有思维链

**模糊判定 (语义, 非字数)**: 能否从输入直接写出可验收标准? 写不出 = 模糊 → brainstorm.
(废除旧版 `len(input.split()) < 8`: split 按空格切词, 对中文输入恒为 1, 判定失效)

**护栏是地板, 不是天花板** (铁律[分诊]):

| 硬护栏 (不可击穿的下限) | 最低路径 |
|---|---|
| ≥3 模块需求 | roadmap |
| 跨模块改动 / 预估 ≥5 文件 | Refactor |
| 用户显式声明生产事故 | Hotfix (唯一免审议, 直接进) |

审议只允许在地板之上加码 (Quick 判成 Feature 可以), 不允许低于地板 (System 级判成 Quick 禁止).

## 中途 re-route (只升不降)

路径不在入口一锤定音. sprint 执行中证据与路径不符 → 重走审议, **只允许升级** (Quick→Feature→Refactor→System):

- **机械触发** (index-updater hook): sprint 改动文件数超路径上限 (Quick>3 / Feature>10) → 写 `next_action=re-route`
- **语义触发** (agent 自查): checklist 膨胀 >50% / 发现跨模块耦合 / design 关键假设被推翻
- **动作**: 重走审议 → route-note 追加 `## Re-route` 段 + `_index.route_history` 记一条 → **补上新路径欠的 stage** (如升 Refactor 需补 runtime-verify + polish + worktree)
- **降级禁止**: 降级 = 给 agent 逃避门禁开合法通道. 确需降级只能用户显式批准

## 写入路由 (铁律[零写入] 红黄绿区)

| 区 | 条件 | 执行者 |
|---|---|---|
| 绿 | 单文件 ≤30 行无跨模块影响, 或 Hotfix/Quick | 主 agent 直接做 |
| 黄 | 单模块 Feature/Bugfix | Agent subagent, worktree 可选 |
| 红 | Refactor/System 或并行 ≥2 写者 | subagent + `isolation: worktree` 强制 |

## References (按需 Read, 不要预加载)

| 场景 | Read |
|---|---|
| 进入某 stage 前看详细工作流 / 数据目录 | `references/stages.md` |
| 选编排机制 (subagent / ultracode / /goal / Agent Team) | `references/orchestration.md` |
| 查 hook 联动 / compound 联动 / 项目级例外 | `references/hooks.md` |
| 某 stage 该用哪个插件 / 插件与流程冲突 | `references/plugins.md` (v9.9.0 U6) |

## 最小循环提醒

- plan/design: 第一条 message 加 "ultrathink"; critic 多轮 (max = `_index.plan_critique_max_rounds`); System/Refactor 可设 `_index.plan_model: fable` 切 fable-5 审议 (贵, opt-in)
- impl: 按红黄绿区路由写入; validation Bash 的 PostToolUse/PostToolUseFailure 分别写 pass/fail evidence
- runtime-verify (Refactor/System 强制 · Feature 可选): /athena-runtime-verify 用 `/goal` 实跑 + 自测自改, 产出 runtime-verify.md (delivery-gate 验); `vm_available=true` 时环境矩阵加远程 VM 实跑 (athena-vm)
- review: 并行 reviewer + spec-compliance 返回结果; 主 agent 合并 passN.md 后再跑 evaluator, 最后由主 agent更新 `_index.next_action`
- ship: delivery-gate 强制门禁 (generator lifecycle / checklist / evidence / roadmap / latest passN PASS / cleanup / architecture)
