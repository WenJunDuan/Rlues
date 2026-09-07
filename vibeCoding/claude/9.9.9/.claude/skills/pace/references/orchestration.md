# PACE References · CC Orchestration (9.9.9)

选机制按当前工具能力与授权；阶段顺序只见 [stages.md](stages.md)，持久恢复与整合只见 [execution-contracts.md](execution-contracts.md)。CC-only 是完整路径，多平台是可选增强。

## 原生机制

| 工作 | CC 入口 | 边界 |
|---|---|---|
| 绿区 | 主 agent | 阶段合同仍适用 |
| 黄区 Feature | Agent generator | 单写者可用当前 checkout |
| 红区 R/S 或 ≥2 writer | Agent + 原生 `isolation: worktree` | 主 agent 先核对基线/未提交输入与允许写集 |
| 独立审查 | 当前原生 review，否则 Agent 只读 reviewer | 不要求 CX；只读任务不套 generator 记账 |
| 长任务 | 当前入口支持且用户已授权的 `/goal` | 无该能力可在原生会话继续；不建第二循环 |
| 定时任务/团队/workflow | 对应已可用原生入口 | 明确任务收益与用户授权后使用，不是默认前提 |

## spawn-binding-handshake

writer 每次派发串行绑定：
1. 冻结新 writer 派发，记录现有 Start/assignment ID；任务消息给 role、task_name、sprint_slug、绝对工作目录、基线、允许写集、输出和验收。
2. 新 writer 首先 `pwd` 核对工作目录，只读准备并报告 ready；收到主 agent 的真实 ID 绑定通知前不修改。原生工具有工作目录字段则每次显式填写；Bash 以该绝对目录执行。
3. 主 agent 取 Agent 返回的真实 ID，并匹配本次唯一未绑定的 SubagentStart。不能以任务昵称、显示标题、队列序号猜 ID；匹配不唯一就不放行。
4. 用现有命令绑定（参数均来自实际返回/任务）：
   `node ~/.claude/hooks/subagent-tracker.cjs assign --cwd <absolute-worktree> --agent-id <actual-id> --task-name <task-name> --role generator`
   回读 subagent-assignments.jsonl，核对真实 agent_id 与 Start 冻结的 sprint_slug。
5. 按 execution-contracts 保存恢复事实，再经当前原生消息或恢复入口通知已绑定。无消息工具时，仅在 writer 可后台执行、双方共享账本且 writer 能核对自身真实 ID 时，按派发前约定有界只读轮询 assignment，唯一匹配自身 ID+sprint+task_name+role 后才放行；超时/歧义不写。入口若只能前台执行，先让准备调用返回，再恢复同一真实 ID；无安全入口不能跳过绑定先写。精确 schema 与条件见 [门禁合同速查](gate-contracts.md#writer--start--assignment--stop)。
6. 已绑定 writer 才能并行；后续派发重复此握手。完成必须匹配独立 SubagentStop 与实际产物，只有 Start/assignment 不算完成。

只读 architect/reviewer 使用原生身份与审查记录，禁止伪造 generator 事件。writer 不是唯一写者，不回滚他人；冲突交指定整合者处理。

## worktree 与清理

主 agent 先确保工作树含实际待改内容；Git worktree 默认不会携带 dirty 文件，明确提交或受控传递增量并校验。原生 `isolation: worktree` 是 CC 能力，不把 Codex 工具名抄入。
默认不注册 WorktreeCreate/Remove hook；其 override 语义需独立验证。生命周期用原生 Start/Stop 和 `git worktree list` 核对。
polish 可在既有实现 worktree 由串行唯一 writer 完成，不额外嵌套隔离；共享 `.ai_state` 始终主 agent 写。repo 外安装态无 worktree 隔离效果时设已约定例外、逐文件备份、单写者串行。
review/ship 之前不自动 push、merge、建 PR 或丢弃 worktree；这些动作按用户有效授权与 delivery gate 执行。清理前验证产物已整合或保留。

## 可选跨端交接

用户选择且实际安装对应插件后才使用其当前入口；不把 `/codex:transfer` 或其他厂商账号作为 CC 必需项。交接先 checkpoint，再给可访问代码和 hash；接收端按 state-contract 现场恢复。协作端失联保留实际进度，本端继续可完成的授权工作，未知结果不算通过。

原生语法依据：[Subagents](https://code.claude.com/docs/en/sub-agents)、[Settings](https://code.claude.com/docs/en/settings)、[Hooks](https://code.claude.com/docs/en/hooks)。版本与承重实测边界见 [platform-contracts.md](platform-contracts.md)。
