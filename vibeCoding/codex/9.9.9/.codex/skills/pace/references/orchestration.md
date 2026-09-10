# PACE References · Orchestration (v9.9.9, Codex)

> 编排机制选型. 铁律[四原语]: Workflow 统领 · SubAgent 执行 · Skill 赋能 · MCP 连接.

## PACE × 原语路由表

| 任务形态 | CX 机制 | 边界 |
|---|---|---|
| 绿区 (定义以 stages.md impl 段为单一真相; 2026-07-28 起 ≤3 文件且合计 ≤150 行, 或 Hotfix/Quick/Bugfix) | 主 thread 可直接实施 | 仍需验证与证据 |
| 黄区 (单模块 Feature) | `spawn_agent` | 单写者, worktree 可选 |
| 红区 (Refactor/System / 并行 ≥2 写者) | 主 thread 创建 worktree 后 `spawn_agent` | 任务消息携带 worktree 绝对路径 |
| 多个独立切片 | 多次 `spawn_agent` | 不超过当前线程上限, 文件写集不得重叠 |
| 长任务跨 turn 完成条件 | Goals | 仅在用户显式要求 Goal 或平台工作流已创建 Goal 时使用 |
| 定时任务 | 当前界面原生 automation（若有）；CLI 用已授权系统调度 | 用户请求后才创建，不自建第二续跑循环 |

## 当前原生协作工具

只使用当前界面提供的四个工具:

- `spawn_agent({task_name, message})`: 启动有界子任务
- `send_message({target, message})`: 给现有 agent 发送上下文, 不触发新 turn
- `followup_task({target, message})`: 给空闲 agent 新任务并触发 turn
- `wait_agent({timeout_ms})`: 等待 agent 邮箱更新

不要把 agent TOML 路径当 shell 命令, 不使用 CLI 风格 cwd 参数、已退场的任务分派动词或通用 shell 等待词代替原生协作工具.

官方能力说明：[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)。调用参数以当前界面 schema 为准，版本文档不代替现场验证。

## Spawn binding handshake

hook 只知道原生生命周期里的真实 `agent_id`; `task_name` / `role` 只存在于主 thread 的任务意图中. 两者必须在每次 spawn 后显式绑定, 禁止按顺序、名称或猜测补账.

**hotfix2 W40: 握手只对 writer/generator 角色执行** — ship 只消费 generator 链, 只读角色 (architect/reviewer/docs_researcher/explorer) 按需 spawn，不冻结不记 assignment；退役角色不得调度。writer spawn 使用以下串行握手; **只串行绑定窗口**, 已绑定 agent 可继续并发执行:

1. **冻结新 spawn**: 同一主 thread 同时只允许一个未绑定 spawn. 读取当前 sprint slug 与已有 `subagent-assignments.jsonl` 的 `agent_id` 集合.
2. **记录 raw boundary**: 在调用 `spawn_agent` 前, 记录 `subagent-events.jsonl` 当前完整行数 `N` (文件不存在则 `N=0`). 后续只检查第 `N+1` 行起的增量, 不重绑旧事件.
3. **启动但先不执行**: `spawn_agent.message` 必须携带 `task_name`、`role`、`sprint_slug`、允许写集, 与**全部任务内容 (内联在 message, 不落盘任务书 — CODEX-TASK.md 类自造文档禁止, 见 stages.md 文书预算)**, 并明确要求 agent 在收到主 thread 的 `BOUND` 消息前不得开始修改目标文件.
4. **等待唯一 Start**: 有界等待 hook 写入增量; 严格解析 raw event schema v1, 在当前 sprint 内筛选尚未出现在 assignment ledger 的 `SubagentStart`. 必须得到**恰好一条 Start 且恰好一个新 `agent_id`**. `spawn_agent` 返回 target/id 时还必须与该 id 一致.
5. **fail closed**: 到达等待上限仍为 0 条, 出现 >1 条、重复 Start、畸形行或 id 不一致时, 立即向已知 target 发送 `STOP: binding failed`, 记录 block reason, 停止本轮编排; 不创建猜测 assignment, 不继续 spawn.
6. **追加 assignment schema v1**: 主 thread 向 `sprints/{sprint_slug}/subagent-assignments.jsonl` 追加且只追加一行:

   ```json
   {"schema_version":1,"agent_id":"<raw Start.agent_id>","task_name":"<spawn task_name>","role":"<declared role>","sprint_slug":"<current sprint>","timestamp":"<UTC ISO-8601>"}
   ```

7. **放行并继续**: assignment 持久化后, 用 `send_message` 向该 target 发送 `BOUND <agent_id>; proceed`。无消息工具时，仅在 writer 可后台执行、双方共享账本且 writer 能核对自身真实 ID 时，按派发前约定有界只读轮询 assignment，唯一匹配自身 ID+sprint+task_name+role 后才放行；超时/歧义不写。前台入口先准备返回再原生恢复同一真实 ID，无安全入口则保持未绑定。此时才开始下一个绑定窗口；精确条件见 [门禁合同速查](gate-contracts.md#writer--start--assignment--stop)。

raw event schema v1 与 assignment schema v1 是两份独立契约: 前者字段为 `schema_version,event,agent_id,agent_type,sprint_slug,timestamp`; 后者字段为 `schema_version,agent_id,task_name,role,sprint_slug,timestamp`. Gate 只通过 `agent_id + sprint_slug` 连接, 不把 `agent_type` 当 `role`.

## worktree 边界 (红区)

`spawn_agent` 没有 cwd 参数. 正确流程:

1. 主 thread 创建 worktree, 记录绝对路径与允许写集.
2. `spawn_agent.message` 写明: worktree 绝对路径、禁止触碰的路径、验收命令.
3. agent 第一个命令执行 `pwd`; 后续每个 shell 调用显式设置该 worktree 为 `workdir`.
4. 主 thread 用 `git -C <worktree> status --short` 与 diff 复核边界.
5. 多写者只分派互斥写集; 共享状态文件由主 thread 串行更新.
6. worktree 产物经主 thread ff 合并进 main 并复验通过后，立即 `git worktree remove` 并删临时分支（2026-09-07 用户裁定），不保留待审壳；返工时重建新 worktree。清理前核对分支为 main 祖先且产物已整合。

review/ship 之前不自动 push 或建 PR；这些动作仍按用户有效授权与 delivery gate 执行。

这是可审计的协作约束, 不是 Codex 提供的机械 cwd 隔离. hook 不得声称能通过解析不存在的 `--cwd` 参数强制它.

## 只读 agent 与落盘所有权

- `architect` / `reviewer` / `pr_explorer` 只返回完整结果（reviewer fallback 的 markdown 由主 thread 原样落盘，`native_output_ref` 指向 `reviews/_native/{id}.md`）。
- 不要 spawn critic / evaluator / spec-compliance。
- 一次本端原生 `/review` 或单个独立只读 reviewer；只有真实异步调用才设置 `await-review-result`，同步结果直接接收。
- writable generator / polish worker 只改任务允许写集; `.ai_state` 默认仍由主 thread 维护。握手只对 writer/generator。

## Goals · Sisyphus 执行层

长任务完成条件使用: 可测终态 + 证据展示 + 预算/停止条件. ship 前核对 Goal 是否真实达成.

| 路径 | 推荐承载范围 |
|---|---|
| System | impl → runtime-verify |
| Refactor | impl + runtime-verify |
| Feature | 可选 runtime-verify |
| Bugfix/Quick/Hotfix | 通常不用 Goal |

护栏:

1. loop 内必须有能判失败的 test/typecheck/delivery-gate.
2. 必须写最大迭代数或明确终止条件.
3. 状态落 `.ai_state`; 不能只留在对话上下文.
4. 重复阻塞时保留 stderr 与已试路径, 不伪报完成.

## CC ↔ CX 移交

CC 与 CX 对齐 PACE 语义和 `.ai_state`，不要求工具逐项对称。只在明确收益且实际可用时跨端；CX-only 由本端完成。移交前 checkpoint，接手者按 [恢复与整合合同](execution-contracts.md) 核对真实基线、未提交增量、原生任务与证据，不依赖外端口头 PASS。

## 长任务三分法

| 目标 | CX 机制 | 边界 |
|---|---|---|
| 每 N 分钟执行 | 当前可用原生 automation 或已授权系统调度 | 用户明确请求才设，避免重复任务 |
| 外部事件触发 | webhook / CI → `codex exec` | 外部系统负责投递 |
| 持续到条件满足 | Goals | 必须有硬验证与停止条件 |

## 平台差异

| 能力 | CC | CX |
|---|---|---|
| worktree 隔离 | 可用 CC 当前提供的 isolation 机制 | 主 thread 建 worktree + 任务携带绝对路径 |
| 多 agent | CC 当前提供的 subagent 机制 | `spawn_agent` / `send_message` / `followup_task` / `wait_agent` |
| hooks | CC hook 事件与 payload | Codex hooks 可覆盖 shell、`apply_patch` 与部分 MCP; 以官方 schema 和实测为准 |
| 状态真相 | `.ai_state` | `.ai_state` |

Codex hooks 官方说明:
https://learn.chatgpt.com/docs/hooks
