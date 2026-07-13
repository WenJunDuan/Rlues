# PACE References · Orchestration (v9.9.1)

> 编排机制选型. 铁律[四原语]: Workflow 统领 · SubAgent 执行 · Skill 赋能 · MCP 连接.
> 选机制前先读本表, 不要凭直觉 spawn.

## PACE × 原语路由表 (M3)

| 任务形态 | CC 机制 | 触发方式 |
|---|---|---|
| 绿区 (单文件 ≤30 行 / Hotfix / Quick) | 主 agent 直接做 | — |
| 黄区 (单模块 Feature/Bugfix) | Agent subagent (`generator` 等) | Agent tool |
| 红区 (Refactor/System / 并行 ≥2 写者) | Agent subagent + `isolation: worktree` | Agent tool |
| 超大规模 (≥5 个独立可切片同构子任务) | Dynamic Workflows | prompt 含 `ultracode` |
| 长任务跨 turn 完成条件 | /goal | `/goal <完成条件>` |
| **定时轮询 (盯 CI / 定期 triage)** | /loop + cron 工具 | `/loop <interval> <prompt>` (2.1.72+ GA) |
| **外部事件驱动 (CI 失败 push 进来)** | Channels | research preview (2.1.80+), **stable 不用** |
| 后台长跑 review/调研 | background subagent | Agent frontmatter `background: true` |

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

**回退链**: workflows 被禁用 (env `CLAUDE_CODE_DISABLE_WORKFLOWS` / Enterprise 默认关) → 退回 Agent subagent 编排, 流程不变.

## /goal · Sisyphus 原生执行层 (M5)

长任务用 `/goal <完成条件>` 设定目标 (CC 2.1.139+), 替代 prompt 层"不完成不许停"约束, 承载铁律[Sisyphus]. ship 前核对 goal 达成.

**机制** [官方 code.claude.com/docs/en/goal]: 每 turn 后由独立小模型 (默认 Haiku) 判停 — maker 不给自己批作业. **evaluator 只读 transcript, 不跑命令不读文件** → 条件必须写成"Claude 的输出能演示的东西", 让 Claude 把证据晒进 transcript.

**条件三件套** (官方, 上限 4000 字符):
1. 可测终态: 测试结果 / build exit code / 文件计数 / 空队列
2. stated check (Claude 怎么证明): 如 "找到数字最大的 reviews/passN.md, 核对最终 `VERDICT: PASS`"
3. 约束: 路上不许动什么 + **turn 上限护栏** (如 "Stop after 30 turns" — /goal 无内建 token 预算, 上限必写)

**非交互入口**: `claude -p "/goal <条件>"` 单命令跑到完成 (夜间/脚本姿势).

## /goal 按 PACE 级别承载 (M5b, v9.8.0)

| 路径 | /goal 用法 |
|---|---|
| System | 创建完整 Sprint, /goal 承载 impl→runtime-verify 全程; agent 在 loop 内自驱 (自己给自己提要求) |
| Refactor | /goal 承载 impl + runtime-verify |
| Feature | runtime-verify 可选, 做则 /goal 承载该环 |
| Bugfix/Quick/Hotfix | 不用 /goal (单测够 / 救火) |

执行者: 默认 CC /goal (有状态 loop + 自带 supervisor + 订阅内).
codex 特例: System 级密集测试想省 token/隔离 → `/codex:transfer` 移交 CX 端 (见下 M5c), opt-in.
完成条件三件套: 可测终态 + stated check (怎么晒进 transcript) + turn 上限护栏.

## CC↔CX 移交 · /codex:transfer (v9.9.0, M5c)

codex-plugin-cc **v1.0.5 (2026-06-23)** 新增 `/codex:transfer`: 把当前 CC 会话移交为**持久 Codex 线程**
[github.com/openai/codex-plugin-cc/releases/tag/v1.0.5]. 这部分解锁了 U5 五五路由:

| 场景 | 用法 |
|---|---|
| System 级密集测试想省 CC token | impl 完成后 `/codex:transfer`, CX 端跑 runtime-verify 重测试环 |
| CC 订阅额度耗尽, 任务未完 | transfer 后 CX 续跑, .ai_state 状态两端共享 (文件即真相) |
| 不适用 | plan/design 审议 (要 ultrathink/critic 链路, 留在 CC); review 三件套 (agents 定义在 CC) |

约束: 要求 codex-plugin-cc ≥1.0.5 (v1.0.4 修了 /codex:rescue Skill 递归, 不要用更旧版).
移交前先 /athena-checkpoint 固化 _index — transfer 换执行者, .ai_state 是唯一记忆连续体.

## 长任务三分法 (M14) [官方 scheduled-tasks 文档]

| 你要的是 | 用 | 边界 (写清楚, 防止当 daemon 用) |
|---|---|---|
| **轮询**: 每 N 分钟干一次 | `/loop` | session-scoped (关终端即灭) · 任务 3 天自动过期 · ≤50/session · 最小间隔 1min · **它不是 daemon**, 真持久化用系统 cron / Desktop scheduled tasks |
| **事件**: 外部系统 push 进来 | Channels | research preview, Bedrock/Vertex 不可用; stable 轨不用, exp 轨另册 |
| **干到条件满足** | `/goal` | 见 M5 |

**loop 设计三问** (任何 loop 形态上线前自答):
1. loop 里有没有能说 no 的东西? (test / typecheck / delivery-gate — 没有硬验证的 loop 会安静地失败并持续烧钱)
2. 预算护栏在哪? (max fires / max iterations / turn 上限 — 必须有硬数字)
3. 状态落盘在哪? (不落盘的 loop 是失忆复读机 — Athena 答案: .ai_state)

**loop 失败模式速查** (借 cobusgreyling/loop-engineering failure-modes; 开环前对照):

| 失败模式 | 症状 | Athena 对策 |
|---|---|---|
| 失控空转 (runaway) | 撞不到完成条件无限跑 | turn 上限护栏 + /goal supervisor 判停 |
| 静默假过 (silent-pass) | supervisor 被"我测过了"骗过 | 完成条件写成"晒命令+输出进 transcript", 只认演示 |
| 上下文腐化 (context-rot) | 长 loop 后期偏离原始 design | 状态落 .ai_state + /athena-checkpoint 固化接续点 |
| 成本爆炸 (cost-blowout) | token/时间烧穿预算 | runtime-verify Step 0 预算护栏硬数字 (loop-cost 思路) |

## Agent Teams (opt-in, 非发布依赖)

仍 experimental (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`), 默认关闭. 仅在用户明确批准后用于 System/Refactor 的并行研究、独立 review 或互斥模块; 3–5 teammates, 禁同文件写入, 禁 nested team. Team task list 只做运行时协调, `.ai_state/checklist.yaml` 仍是项目真相, delivery-gate 不依赖 team 状态.

## worktree 规则速查

- ⚠️ **CC 2.1.198 行为变更**: 后台 agent 在 worktree 完成工作后**默认自动 commit+push+开 draft PR**, 不等确认 —
  这绕过 review→ship 门禁顺序. Athena 对策: pre-bash-guard 在 stage != ship 时 block `git push` (v9.9.0);
  部署后实测一次后台 worktree 流, 确认自动 PR 行为被拦或已在设置中关闭.
- 红区强制; 黄区可选; 绿区不用
- `worktree.baseRef=head`; 红区调用 Agent 时显式传 `isolation: worktree`, 黄区 generator 不强制隔离
- subagent-worktree-check hook (PreToolUse Agent) 机械强制, 违规 block
- 默认不注册 WorktreeCreate/Remove hook；其存在会完全替代 Claude Code 原生 Git worktree
- 生命周期用 SubagentStart/Stop + `git worktree list` 现场证明; dirty 未提交内容不会自动进入新 worktree
