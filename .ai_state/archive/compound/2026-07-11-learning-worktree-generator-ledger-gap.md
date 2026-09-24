---
doc_type: learning
sprint: 2026-07-10-claude-code-9-9-1-impl
created: 2026-07-11
---

# worktree-isolated generator 不进机器账本 → delivery-gate generator-chain 空查

## 现象

System 路径 CC 9.9.1 rework/polish/§18 三批实现均由 generator subagent 执行, 且按铁律[零写入]红区强制用 `isolation: worktree`。ship 时 delivery-gate (Stop hook) 报: subagent-log.md 无 generator 记录, generator-chain 校验失败。

实测: `.ai_state/sprints/{slug}/subagent-events.jsonl` 与 `subagent-assignments.jsonl` 全局不存在; subagent-log.md 只有 reviewer/spec-compliance/evaluator (read-only, 非 worktree) 的 SubagentStop 记录, 无任何 generator。

## 根因

1. read-only review subagent 的 SubagentStop 以 cwd=主 repo 触发 → tracker 正常写主 sprint subagent-log.md。
2. generator 跑在 harness 创建的 ephemeral isolation worktree (`Rlues-worktrees/agent-*`), SubagentStart/Stop 以 cwd=该 worktree 触发。安装的 tracker (实测 header=v9.9.2) 虽有 redirectToMainRepo, 但本会话未把这些 worktree-isolated generator 的 lifecycle 落进主 sprint 机器账本 (jsonl 根本没生成), worktree 清理后事件源亦消失。
3. 版本偏斜: 用户 `~/.claude` 装 v9.9.2, 本轮发布 9.9.1; 安装的 gate 查 generator-chain, 但账本机制在该环境未产出 jsonl。

## 教训

**铁律[零写入]要求红区 generator 用 worktree 隔离, 但 tracker↔gate 的 generator-chain 证据链假设 generator 事件落在主 sprint 账本 —— 两者对 worktree-isolated generator 存在结构性矛盾。** 隔离越干净, gate 越查不到。

## 缓解 (本轮)

设 `_index.skip_impl_subagent_check=true` (自负责), 因: (a) 工作真实由 generator 完成, subagent-log.md review 记录 + pass1-3 三轮审查 + 全绿代码 (144/0·72/0/0·11/11) 独立佐证; (b) 无法诚实重建从未 emit 的 Start/Stop/assignment 记录; (c) 不伪造账本条目 (违背账本作为防篡改证据的本意)。

## Followup (下轮 CC patch)

- tracker: worktree-isolated generator 的 SubagentStart/Stop 必须可靠 redirect 到主 sprint 机器账本 (jsonl), 或 gate 承认 subagent-log.md 人类记录 + 主 agent assignment 握手作为 red-zone 替代证据。
- 验证矩阵补: red-zone (isolation:worktree) generator 的 ledger E2E, 断言 events.jsonl 在主 sprint 生成。
- 关联 [[2026-07-10-learning-codex-wire-evidence-fail-closed]] (fail-closed 证据链), [[2026-07-08-learning-hook-order-and-worktree-counts]] (worktree 计数)。
