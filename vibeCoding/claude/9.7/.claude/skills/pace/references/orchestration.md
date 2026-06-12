# PACE References · Orchestration (v9.7.0)

> 编排机制选型. 铁律[三原语]: Workflow 统领 · SubAgent 执行 · Skill 赋能.
> 选机制前先读本表, 不要凭直觉 spawn.

## PACE × 原语路由表 (M3)

| 任务形态 | CC 机制 | 触发方式 |
|---|---|---|
| 绿区 (单文件 ≤30 行 / Hotfix / Quick) | 主 agent 直接做 | — |
| 黄区 (单模块 Feature/Bugfix) | Task subagent (`generator` 等) | Task tool |
| 红区 (Refactor/System / 并行 ≥2 写者) | Task subagent + `isolation: worktree` | Task tool |
| 超大规模 (≥5 个独立可切片同构子任务) | Dynamic Workflows | prompt 含 `ultracode` |
| 长任务跨 turn 完成条件 | /goal | `/goal <完成条件>` |
| 后台长跑 review/调研 | background session | Task + 后台 |

## ultracode · Dynamic Workflows (M4)

**触发词**: prompt 含 `ultracode` (2.1.154 GA, 2.1.160 改名; "workflow" 一词不再触发) [官方 changelog]

**适用**:
- System/Refactor 且 ≥5 个独立可切片子任务 (批量重命名 / 批量迁移 / 大规模审计)
- 子任务之间无依赖、无共享写入

**不适用**:
- 互相依赖的任务 (主 agent 顺序编排)
- 涉及 .ai_state 写入的任务 (主 agent 集中管 state)
- 绿区 / 黄区 (杀鸡用牛刀)

**边界 (官方约束)**:
- workflow 内 subagent 固定 `acceptEdits` 权限模式
- 中间结果留在 script 变量, 不进主上下文
- ≤16 并发 / ≤1000 agent 总量; 可恢复
- **产物不豁免**: workflow 跑完仍进 Athena review 三件套 (reviewer + spec-compliance + evaluator)

**回退链**: workflows 被禁用 (env `CLAUDE_CODE_DISABLE_WORKFLOWS` / Enterprise 默认关) → 退回 Task subagent 编排, 流程不变.

## /goal · Sisyphus 原生执行层 (M5)

长任务用 `/goal <完成条件>` 设定目标 (CC 2.1.139+), 替代 prompt 层"不完成不许停"约束, 承载铁律[Sisyphus]. ship 前核对 goal 达成.

## Agent Teams (不接入, Out of Scope)

仍 experimental (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`), token ×N, 无 dogfood 数据. 不写入任何流程. 待 GA 后再评估.

## worktree 规则速查

- 红区强制; 黄区可选; 绿区不用
- `isolation: worktree` 写在 subagent frontmatter (generator 已带)
- subagent-worktree-check hook (PreToolUse Task) 机械强制, 违规 block
- WorktreeCreate/Remove hook 自动维护 worktrees.yaml + `_index.active_worktrees`
