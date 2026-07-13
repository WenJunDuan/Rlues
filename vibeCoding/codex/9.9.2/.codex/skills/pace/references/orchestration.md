# PACE References · Orchestration (v9.9.1, Codex)

> 编排机制选型. 铁律[四原语]: Workflow 统领 · SubAgent 执行 · Skill 赋能 · MCP 连接.

## PACE × 原语路由表

| 任务形态 | CX 机制 | 边界 |
|---|---|---|
| 绿区 (单文件 ≤30 行 / Hotfix / Quick) | 主 thread 可直接实施 | 仍需验证与证据 |
| 黄区 (单模块 Feature/Bugfix) | `spawn_agent` | 单写者, worktree 可选 |
| 红区 (Refactor/System / 并行 ≥2 写者) | 主 thread 创建 worktree 后 `spawn_agent` | 任务消息携带 worktree 绝对路径 |
| 多个独立切片 | 多次 `spawn_agent` | 不超过当前线程上限, 文件写集不得重叠 |
| 长任务跨 turn 完成条件 | Goals | 仅在用户显式要求 Goal 或平台工作流已创建 Goal 时使用 |
| 定时轮询 | `codex exec` + 系统 cron | Automations 是 Codex app 能力, 不假定 CLI 内置 |

## multi-agent v2 原生工具 (Codex 0.144.1)

只使用当前界面提供的四个工具:

- `spawn_agent({task_name, message})`: 启动有界子任务
- `send_message({target, message})`: 给现有 agent 发送上下文, 不触发新 turn
- `followup_task({target, message})`: 给空闲 agent 新任务并触发 turn
- `wait_agent({timeout_ms})`: 等待 agent 邮箱更新

不要把 agent TOML 路径当 shell 命令, 不使用 CLI 风格 cwd 参数、已退场的任务分派动词或通用 shell 等待词代替原生协作工具.

官方工具 schema:
https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core/src/tools/handlers/multi_agents_spec.rs#L78-L112

## Spawn binding handshake

hook 只知道原生生命周期里的真实 `agent_id`; `task_name` / `role` 只存在于主 thread 的任务意图中. 两者必须在每次 spawn 后显式绑定, 禁止按顺序、名称或猜测补账.

每次 spawn 使用以下串行握手; **只串行绑定窗口**, 已绑定 agent 可继续并发执行:

1. **冻结新 spawn**: 同一主 thread 同时只允许一个未绑定 spawn. 读取当前 sprint slug 与已有 `subagent-assignments.jsonl` 的 `agent_id` 集合.
2. **记录 raw boundary**: 在调用 `spawn_agent` 前, 记录 `subagent-events.jsonl` 当前完整行数 `N` (文件不存在则 `N=0`). 后续只检查第 `N+1` 行起的增量, 不重绑旧事件.
3. **启动但先不执行**: `spawn_agent.message` 必须携带 `task_name`、`role`、`sprint_slug`、允许写集, 并明确要求 agent 在收到主 thread 的 `BOUND` 消息前不得读取或修改任务文件.
4. **等待唯一 Start**: 有界等待 hook 写入增量; 严格解析 raw event schema v1, 在当前 sprint 内筛选尚未出现在 assignment ledger 的 `SubagentStart`. 必须得到**恰好一条 Start 且恰好一个新 `agent_id`**. `spawn_agent` 返回 target/id 时还必须与该 id 一致.
5. **fail closed**: 到达等待上限仍为 0 条, 出现 >1 条、重复 Start、畸形行或 id 不一致时, 立即向已知 target 发送 `STOP: binding failed`, 记录 block reason, 停止本轮编排; 不创建猜测 assignment, 不继续 spawn.
6. **追加 assignment schema v1**: 主 thread 向 `sprints/{sprint_slug}/subagent-assignments.jsonl` 追加且只追加一行:

   ```json
   {"schema_version":1,"agent_id":"<raw Start.agent_id>","task_name":"<spawn task_name>","role":"<declared role>","sprint_slug":"<current sprint>","timestamp":"<UTC ISO-8601>"}
   ```

7. **放行并继续**: assignment 持久化后, 用 `send_message` 向该 target 发送 `BOUND <agent_id>; proceed`. 此时可开始下一个 spawn 的绑定窗口; 之前已绑定的 agents 可并发运行.

raw event schema v1 与 assignment schema v1 是两份独立契约: 前者字段为 `schema_version,event,agent_id,agent_type,sprint_slug,timestamp`; 后者字段为 `schema_version,agent_id,task_name,role,sprint_slug,timestamp`. Gate 只通过 `agent_id + sprint_slug` 连接, 不把 `agent_type` 当 `role`.

## worktree 边界 (红区)

`spawn_agent` 没有 cwd 参数. 正确流程:

1. 主 thread 创建 worktree, 记录绝对路径与允许写集.
2. `spawn_agent.message` 写明: worktree 绝对路径、禁止触碰的路径、验收命令.
3. agent 第一个命令执行 `pwd`; 后续每个 shell 调用显式设置该 worktree 为 `workdir`.
4. 主 thread 用 `git -C <worktree> status --short` 与 diff 复核边界.
5. 多写者只分派互斥写集; 共享状态文件由主 thread 串行更新.

这是可审计的协作约束, 不是 Codex 提供的机械 cwd 隔离. hook 不得声称能通过解析不存在的 `--cwd` 参数强制它.

## 只读 agent 与落盘所有权

- `critic` / `architect` / `reviewer` / `spec-compliance` / `pr_explorer` / `evaluator` 只返回完整结果, 不创建或修改文件.
- 主 thread 负责把结果串行写入 `sprints/{current_sprint_slug}/...` 并更新 `_index.md`.
- review 先并行跑 reviewer + spec-compliance; 主 thread 合并 `passN.md`; evaluator 后跑并读取合并结果.
- writable generator / polish worker 只改任务允许写集; `.ai_state` 默认仍由主 thread 维护.

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

CC 与 CX 对齐 PACE 语义和 `.ai_state` 文件, 不要求工具逐项对称. CC 端若使用 `/codex:transfer`, 移交前先 checkpoint; CX 端从 `_index.md` 和当前 sprint 恢复, 再按本文件的原生工具继续.

## 长任务三分法

| 目标 | CX 机制 | 边界 |
|---|---|---|
| 每 N 分钟执行 | `codex exec` + 系统调度 | 写最大触发次数 |
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
