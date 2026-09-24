# PACE References · Orchestration (v9.9.0, Codex)

> 编排机制选型. 铁律[三原语]: Workflow 统领 · SubAgent 执行 · Skill 赋能.

## PACE × 原语路由表 (M3)

| 任务形态 | CX 机制 | 触发方式 |
|---|---|---|
| 绿区 (单文件 ≤30 行 / Hotfix / Quick) | 主 thread 直接做 | — |
| 黄区 (单模块 Feature/Bugfix) | spawn_agent (`generator.toml` 等) | multi-agent v2 |
| 红区 (Refactor/System / 并行 ≥2 写者) | `git worktree add` + `spawn_agent --cwd` | multi-agent v2 |
| 超大规模 (≥5 个独立可切片同构子任务) | spawn_agent fan-out (受 `[agents].max_threads` 限) | multi-agent v2 |
| 长任务跨 turn 完成条件 | Goals | `/goal` (0.133+ 默认开启, 全平台 GA) |
| **定时轮询 (盯 CI / 定期 triage)** | `codex exec` + 系统 cron | CLI 无内置定时; Automations 是 **Codex app (GUI) 专属** [官方], CLI 不可用 |
| 后台长跑 review/调研 | assign_task 后台分派 | multi-agent v2 |

## multi-agent v2 工具语义 (0.137 收敛) [官方 release notes]

四个核心动词:
- `spawn_agent` — 派生 subagent (agent toml + prompt; 红区配 `--cwd <worktree>`)
- `send_message` — 与运行中 agent 通信
- `assign_task` — 把任务分派给 agent; **task 不能 assign 给 root agent** (0.137 收敛)
- `wait` — 等待 agent 完成

配置: config.toml `[features].multi_agent = true` (已开), `[agents]` max_threads / max_depth / job_max_runtime_seconds.

> v9.7.0 起编排统一走 multi-agent v2 原生工具, 不再自造编排模板 (增强不取代).

## Goals · Sisyphus 原生执行层 (M5)

长任务用 `/goal <完成条件>` 设定目标 (CX 0.133+ 默认开启, 无需 `features.goals`) [官方 release 0.133], 替代 prompt 层"不完成不许停"约束, 承载铁律[Sisyphus]. ship 前核对 goal 达成.

**护栏** [社区引官方 changelog]: goal continuation 撞 usage limit 或重复 blocker 自动停 (防 token 燃烧). 条件写法同 CC 三件套: 可测终态 + stated check (让 agent 把证据晒进输出) + turn/时间上限.

## Goals 按 PACE 级别承载 (M5b, v9.8.0)

| 路径 | Goals 用法 |
|---|---|
| System | 创建完整 Sprint, Goals 承载 impl→runtime-verify 全程; agent 在 loop 内自驱 (自己给自己提要求) |
| Refactor | Goals 承载 impl + runtime-verify |
| Feature | runtime-verify 可选, 做则 Goals 承载该环 |
| Bugfix/Quick/Hotfix | 不用 Goals (单测够 / 救火) |

执行者: 默认 CX 本平台 Goals (0.133+ 默认开启). 密集测试想隔离/省 token → spawn_agent generator.toml 分派 (multi-agent v2), opt-in.
完成条件三件套: 可测终态 + stated check (怎么晒进对话) + turn 上限护栏.

## CC↔CX 移交 · /codex:transfer (v9.9.0, M5c)

codex-plugin-cc **v1.0.5 (2026-06-23)** 新增 `/codex:transfer` (CC 端命令): 把当前 CC 会话移交为**持久 Codex 线程**
[github.com/openai/codex-plugin-cc/releases/tag/v1.0.5]. 这部分解锁了 U5 五五路由 (CX 端是接收方):

| 场景 | 用法 |
|---|---|
| System 级密集测试想省 CC token | impl 完成后 CC 端 `/codex:transfer`, CX 端跑 runtime-verify 重测试环 |
| CC 订阅额度耗尽, 任务未完 | transfer 后 CX 续跑, .ai_state 状态两端共享 (文件即真相) |
| 不适用 | plan/design 审议 (要 ultrathink/critic 链路, 留在 CC); review 三件套 (agents 定义在 CC) |

约束: 要求 codex-plugin-cc ≥1.0.5 (v1.0.4 修了 /codex:rescue Skill 递归, 不要用更旧版).
移交前先 /athena-checkpoint 固化 _index — transfer 换执行者, .ai_state 是唯一记忆连续体.

## 长任务三分法 (M14)

| 你要的是 | CX 用 | 边界 |
|---|---|---|
| **轮询**: 每 N 分钟干一次 | `codex exec --sandbox workspace-write` + 系统 cron / `codex remote-control` 编排 [官方] | CLI 无内置 /loop; **Automations 是 Codex app (GUI) 专属**, 不在 CLI; 非交互姿势官方钦定 `codex exec` (--full-auto 已 deprecated 会打 warning) |
| **事件**: 外部系统 push 进来 | 无 CC Channels 对等物 | GitHub Actions / webhook → `codex exec` 是事实路径 |
| **干到条件满足** | Goals | 见 M5 |

**loop 设计三问** (任何 loop 形态上线前自答):
1. loop 里有没有能说 no 的东西? (test / typecheck / delivery-gate — 没有硬验证的 loop 会安静地失败并持续烧钱)
2. 预算护栏在哪? (max fires / max iterations — 必须有硬数字)
3. 状态落盘在哪? (不落盘的 loop 是失忆复读机 — Athena 答案: .ai_state)

**loop 失败模式速查** (借 cobusgreyling/loop-engineering failure-modes; 开环前对照):

| 失败模式 | 症状 | Athena 对策 |
|---|---|---|
| 失控空转 (runaway) | 撞不到完成条件无限跑 | turn 上限护栏 + Goals continuation 自动停 |
| 静默假过 (silent-pass) | 完成判定被"我测过了"骗过 | 完成条件写成"晒命令+输出进对话", 只认演示 |
| 上下文腐化 (context-rot) | 长 loop 后期偏离原始 design | 状态落 .ai_state + /athena-checkpoint 固化接续点 |
| 成本爆炸 (cost-blowout) | token/时间烧穿预算 | runtime-verify Step 0 预算护栏硬数字 (loop-cost 思路) |

## 平台差异速查 (vs CC)

| 能力 | CC | CX |
|---|---|---|
| Dynamic Workflows (ultracode) | ✅ 2.1.154+ | ❌ 无对等, 用 spawn_agent fan-out |
| 定时轮询 | ✅ /loop+cron 工具 (session 内 GA) | ❌ CLI 无内置, codex exec + 系统 cron |
| 事件驱动 Channels | 🟡 research preview | ❌ |
| Agent Teams | experimental, 不接入 | ❌ |
| 文件写 hook 拦截 | ✅ PostToolUse(Edit\|Write) | ❌ 仅 Bash [官方], evidence 走降级链 |
| compact hooks | ✅ PreCompact/PostCompact | ✅ 0.129+ 同名事件 |
| Subagent hooks | ✅ SubagentStart/Stop (matcher=agent type) | ✅ 原生事件 [官方], SubagentStop 使用 agent_type / agent_id |

## worktree 规则速查

- ⚠️ **CC 2.1.198 行为变更** (CC 端行为, CX 端 push 门禁同样生效): CC 后台 agent 在 worktree 完成工作后**默认自动 commit+push+开 draft PR**, 不等确认 —
  这绕过 review→ship 门禁顺序. Athena 对策: pre-bash-guard.py 在 stage != ship 时 block `git push` (v9.9.0);
  部署后实测一次后台 worktree 流, 确认自动 PR 行为被拦或已在设置中关闭.
- 红区强制; 黄区可选; 绿区不用
- CX 无 `isolation: worktree` frontmatter, 等价: 主 thread `git worktree add ../wt-{slug} -b wt-{slug}` → `spawn_agent --cwd ../wt-{slug}`
- pre-bash-guard hook 机械强制 (Refactor/System 下 spawn_agent 无 --cwd → block), 并监听 git worktree add/remove 维护 worktrees.yaml
