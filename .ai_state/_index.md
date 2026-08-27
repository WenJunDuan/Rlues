---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.9.3 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.9.3"

# === PACE 路由状态 ===
path: "System"                 # 9.9.8 review contract + hook austerity + future verifier slots
stage: "ship"                  # 用户授权将 9.9.8 推送 origin/main
current_sprint_slug: "2026-08-27-athena-9-9-8"
current_roadmap_slug: "athena-9-9-8"
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 路由审议 (v9.9.0) ===
route_confidence: 0.94             # 用户显式开 9.9.8 System；三切片 roadmap；独立 Claude 复盘但设计作者不自审
route_history: ["2026-07-10 System: CC 9.9.1 redesign from CC 9.9.0 baseline, awaiting Fable5 review", "2026-07-10 System: user-approved impl-first flow; Fable5 post-implementation review remains mandatory", "2026-07-13 System: user-approved Athena 9.9.2 overall architecture upgrade; four primitives + spec-gate + two-tier memory are mandatory", "2026-07-14 System: repair Athena 9.9.3 review findings, full regression, formal review, merge and publish", "2026-07-25 System+roadmap: research-led Athena 9.9.6 prompt architecture refresh for Claude Code and Codex", "2026-07-25 System impl: user authorized Claude review repairs directly in main checkout without worktree", "2026-07-28 System impl 范围扩张 (非 re-route): 用户拍板把 2026-07-27-hotfix-gate-contract 的 A-E 五条并入本 sprint 作 →index-overflow.md#rh-0", "2026-07-28 System impl 红区降级 (用户显式批准): spawn generator 执行 G1-G5 被 subagent-worktree-check.cjs 无条件 block →index-overflow.md#rh-1", "2026-07-29 System impl: 用户授权 hotfix2 W35-W40 安装态同步、真实 sprint 采数、validator 收口与 main 推送；canoni →index-overflow.md#rh-2", "2026-08-27 System: Athena 9.9.8 Thin PACE Control Plane；一次原生 review、hook 红黄绿、有界 ai_state；VM/LaaV 仅保留 o →index-overflow.md#rh-3"]  # re-route ≤10, item ≤160B
plan_model: "fable"                    # "" | "fable" — System/Refactor 的 plan/design 审议切 fable-5 (贵, opt-in)

# === 平台与版本 ===
platforms_enabled: ["both"]       # cc | cx | both
cc_version: "claude-code 2.1.231"
cx_version: "codex-cli 0.150.0"
ag_callable: false                # antigravity (agy) 未安装

# === 平台原生能力 (athena-init 探测) ===
platform_features:
  cc_subagent_task: true          # CC Task tool (always true)
  cc_ultrathink_supported: true   # CC v2.1.68+ ultrathink keyword
  cc_isolation_worktree: true     # 本会话 Agent tool 实测支持 isolation: worktree
  cc_subagent_stop_hook: true     # CC SubagentStop 原生事件
  cc_worktree_hooks: true         # CC WorktreeCreate/Remove 原生事件
  cc_stop_prompt_hook: true       # CC Stop hook prompt 类型 (2026-03+)
  cx_spawn_agent: true            # Codex 0.145.0 native multi-agent v2
  cx_plan_mode_reasoning_effort: true    # Codex 0.145.0
  cx_spawn_agents_on_csv: false   # 当前 surfaced v2 无 CSV fan-out；按实际工具能力判定
  ag_parallel_subagents: false    # Antigravity 并行
  ag_headless_p: false            # agy -p

# === 工具可用性 (athena-init 探测) ===
tools_available:
  context7_cli: false             # npx ctx7 可用
  context7_mcp_cx: false
  augment_mcp_cc: false
  augment_mcp_cx: false
  web_search_cc: true             # CC WebSearch (always true)
  web_search_cx: true             # Codex web_search = "live"
  rg_available: true
  jq_available: true
  agentshield_cli: false          # ECC AgentShield (可选)
  vm_available: false             # v9.9.0: ~/.athena/vm.json 存在且 athena-vm doctor 连通

# === 进度计数 (index-updater hook 自动维护, 不手填) ===
counts:
  features_count: 5
  issues_count: 0
  refactors_count: 1
  systems_count: 12
  requirements_count: 1
  reviews_count: 24
  cleanup_count: 8
  compound:
    learning: 5
    trick: 0
    decision: 4
    explore: 1

# === Pointers (指向最新相关文件) ===
pointers:
  latest_design: "sprints/2026-08-27-athena-9-9-8/design.md"
  latest_review: "sprints/2026-08-27-athena-9-9-8/reviews/implementation-review.md"
  latest_cleanup: "sprints/2026-08-27-athena-9-9-8/cleanup-pass.md"
  latest_brainstorm: ""
  latest_decisions: ["compound/2026-07-28-decision-close-prompt-engineering-direction.md", "compound/2026-07-13-decision-quantum-7-to-2-consolidation.md", "compound/2026-07-13-decision-index-field-audit.md", "compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md"]
  latest_lessons: ["compound/2026-07-28-learning-reserved-ac-labels-silent-exemption.md", "compound/2026-07-14-learning-canonical-install-path-runtime.md", "compound/2026-07-11-learning-worktree-generator-ledger-gap.md", "compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md", "compound/2026-07-08-learning-hook-order-and-worktree-counts.md"]
  latest_architecture_update: "2026-08-27T11:13:37.112Z"
  latest_requirement: "requirements/fullstack-delivery-pack.md"

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
next_action: "ship"
last_subagent: "athena_998_architecture_challenge"
last_subagent_at: "2026-08-27T02:57:33.966970Z"
active_worktrees: []
last_critic_round: 0              # 9.9.8：设计作者不自审
design_changed_after_impl: false

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_min_rounds: 0       # 9.9.8：作者会话 0 轮；独立审查走 review-packet
plan_critique_disabled: true      # 本 sprint 用户要求：写设计的模型不审自己的设计
skip_impl_subagent_check: true    # 用户授权主 agent 在 main checkout 直做 9.9.8；不伪造 generator 生命周期
network_in_polish: true           # polish_worker 是否允许 network
breadcrumb: "on"                 # v9.9.3: per-turn stage breadcrumb; off 可关闭

# === Fingerprint (index-updater 用于 mtime 比对) ===
fingerprint: ""
---

# Athena Project State Index (v9.9.3)

> 本文件由 Athena 自动维护. 不要手工修改 frontmatter 字段以外的部分除非你知道你在做什么.

## 当前状态
> Tier1 会话上下文是工作记忆；Tier2 `.ai_state` 是持久真相。本 `_index` 仅作有界检索路由器，详细历史在 sprint/git。

[由主 agent 在 stage 切换时简短追加]

- 2026-08-27 ship: 9.9.8 推 origin/main。validator 120/0/0。本机 CC/CX 已同步。
- 2026-08-27 leftover: AC11 eval PASS (labeled); 160B overflow on; ~/.claude|codex 9.9.8 synced, user model/effort kept. Targeted packet ready.
- 2026-08-27 rework: F1–F7 已修。validator 106/0/0。待独立复核。F8 eval 为 ship 前置。未同步 ~/.claude|codex。
- 2026-08-27 design：Grok/Codex 已完善 `Thin PACE Control Plane`：一次原生 review、hook 红黄绿（现场复现无害 `rg` pa →index-overflow.md#st-1
- 2026-07-29 ship：hotfix2 已完成提交并推送 `main`（`19dd8d5`）；delivery-gate exit 0，工作树干净，当前 sprint/road →index-overflow.md#st-2
- 2026-07-29 W35-W40 hotfix2：canonical 双端包已同步 ~/.claude 与 ~/.codex（30 个目标，逐文件事务备份）；历史/ →index-overflow.md#st-3
- 2026-07-28 W31-W34 安装态部署已完成：12 个源条目、10 个唯一目标，9 个过期目标更新；两端哈希、语法 →index-overflow.md#st-4
- 2026-07-28 用户主动关闭 9.9.6 prompt-engineering / gate-descaling 方向：原本的改动反复且叙述冗长，后续不再 →index-overflow.md#st-5
- `2026-07-28`: **10bd534 gate-descaling 本地 draft 已同步到当前系统端点**：CC 128 / CX 33 / shared skills 97，管理哈 →index-overflow.md#st-6
- older 当前状态 →index-overflow.md#st-10

## 工具调度建议

根据 `tools_available` + `platform_features`, 主 agent 进入每个 stage 时按下表选工具:

### brainstorm stage
- 主 agent 与用户对话, 不读 compound (创意空间不污染)
- 不 spawn subagent, 不 worktree

### roadmap stage
- 主 agent 调研 + 用户确认
- 输出 items.yaml + roadmap.md

### plan / design stage
- 主 agent 用 ultrathink (CC) / xhigh (CX) 出 design.md 初版
- 作者会话不 spawn critic; R/S 独立挑战从派生 review-packet 开始
- Feature 无固定 design review

### impl stage (subagent 始终用)
- CC: Task `generator` subagent
- CX: native `spawn_agent({task_name,message})`; 先按 `~/.agents/skills/pace/references/orchestration.md` 完成 raw Start → assignment 握手
- Refactor/System: CC 使用平台 isolation；CX 由主线程 `git worktree add`，任务携带绝对路径，agent 验证 `pwd/workdir`
- 并行 ≥ 2 subagent 改文件时: 强制 worktree 隔离

### review stage (一次原生请求)
- 发起一轮 `/code-review` 或平台等价物; `next_action=await-review-result` 期间 Stop 放行
- 结果写入 `reviews/implementation-review.md`（含 `review_run_id` + `native_output_ref`）
- critic / evaluator / spec-compliance 为 stub, 不 live 调度

### polish stage (Refactor/System 强制)
- spawn `polish_worker` (workspace-write, network=true 查最佳实践)
- 产出 cleanup-pass.md

### ship stage
- 主 agent commit + push
- Refactor/System 还需检查 architecture/ 更新 (delivery-gate)

## 历史 (由 pace-continuator hook 自动追加, 最多保留近 10 条)
- `2026-07-25 17:56:21`: stage=impl sprint=2026-07-25-athena-9-9-6-prompt-engineering turn-end
- `2026-07-21 03:21:03`: stage=  sprint=  turn-end
- `2026-07-21 03:18:58`: stage=  sprint=  turn-end
- `2026-07-11 12:59:01`: stage=ship sprint=2026-07-10-claude-code-9-9-1-impl turn-end
- `2026-07-10 13:31:06`: stage=review sprint=2026-07-10-claude-code-9-9-1-impl turn-end
- `2026-07-07 02:24:00`: stage=plan sprint=2026-07-07-f1-orchestrator-framework-design turn-end
- `2026-07-07 01:53:39`: stage=  sprint=  turn-end
