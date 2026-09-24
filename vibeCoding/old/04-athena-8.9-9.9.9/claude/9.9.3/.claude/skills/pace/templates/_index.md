---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.9.3 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.9.3"

# === PACE 路由状态 ===
path: ""                          # Hotfix | Bugfix | Quick | Feature | Refactor | System
stage: ""                         # brainstorm | roadmap | plan | design | impl | runtime-verify | review | polish | ship
breadcrumb: "on"                # v9.9.3 每轮 stage 面包屑注入; "off" 关闭 (fail-open)
current_sprint_slug: ""           # 当前 sprint 目录名, 如 "2026-05-25-jwt-refresh"
current_roadmap_slug: ""          # 仅 roadmap stage 期间填
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 路由审议 (v9.9.3) ===
route_confidence: 0               # 0-1, 主 agent 路由决策摘要中的置信度
route_history: []                 # re-route 记录, 最多 10 条; 详情归 sprint/session-log
plan_model: ""                    # "" | "fable" — System/Refactor 的 plan/design 审议切 fable-5 (贵, opt-in)

# === 平台与版本 ===
platforms_enabled: ["cc"]         # cc | cx | both
cc_version: ""                    # 由 athena-init 探测
cx_version: ""
ag_callable: false                # antigravity (agy) 可调度?

# === 平台原生能力 (athena-init 探测) ===
platform_features:
  cc_subagent_task: true          # 共享字段名保留; CC 当前 Agent tool 可用
  cc_ultrathink_supported: false  # CC v2.1.68+ ultrathink keyword
  cc_isolation_worktree: false    # CC v2.x+ subagent frontmatter isolation: worktree
  cc_subagent_stop_hook: false    # CC SubagentStop 原生事件
  cc_worktree_hooks: false        # CC WorktreeCreate/Remove 原生事件
  cc_stop_prompt_hook: false      # CC Stop hook prompt 类型 (2026-03+)
  cx_spawn_agent: false           # Codex spawn_agent (0.128+)
  cx_plan_mode_reasoning_effort: false   # Codex 0.105.0+ plan_mode_reasoning_effort
  ag_parallel_subagents: false    # Antigravity 并行
  ag_headless_p: false            # agy -p

# === 工具可用性 (athena-init 探测) ===
tools_available:
  context7_cli: false             # npx ctx7 可用
  context7_mcp_cx: false
  augment_mcp_cc: false
  augment_mcp_cx: false
  web_search_cc: true             # CC WebSearch (always true)
  web_search_cx: false            # Codex web_search = "live"
  rg_available: true
  jq_available: true
  agentshield_cli: false          # ECC AgentShield (可选)
  vm_available: false             # v9.9.0: ~/.athena/vm.json 存在且 athena-vm doctor 连通

# === 进度计数 (index-updater hook 自动维护, 不手填) ===
counts:
  features_count: 0               # sprints/ 下 path=Feature 目录数
  issues_count: 0                 # path=Bugfix 目录数
  refactors_count: 0              # path=Refactor 目录数
  systems_count: 0                # path=System 目录数
  requirements_count: 0           # requirements/ 下需求档数 (v9.8.0)
  reviews_count: 0
  cleanup_count: 0
  compound:
    learning: 0
    trick: 0
    decision: 0
    explore: 0

# === Pointers (指向最新相关文件) ===
pointers:
  latest_design: ""               # sprints/{current_sprint_slug}/design.md
  latest_review: ""
  latest_cleanup: ""
  latest_brainstorm: ""
  latest_decisions: []            # 最近 5 个 compound/decision-*.md (按 mtime desc)
  latest_lessons: []              # 最近 5 个 compound/learning-*.md
  latest_architecture_update: ""  # ARCHITECTURE.md 最近更新时间 (UTC ISO-8601, 非文件指针)
  latest_requirement: ""          # requirements/{slug}.md 最新 (v9.8.0)

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
next_action: ""                   # 主 agent / delivery-gate 写: runtime-verify | polish | ship | rework_impl | next_roadmap_item:{slug}
last_subagent: ""                 # SubagentStop hook 仅记录生命周期
last_subagent_at: ""
active_worktrees: []              # 主 agent 现场核对 git worktree list 后维护; hook 不替代原生创建
last_critic_round: 0              # plan stage critic 已跑轮数
design_changed_after_impl: false  # design.md 改后需 re-review

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_min_rounds: 0       # 0=auto (Refactor/System=2, 其余=1); delivery-gate 在 ship 验 design.md 轮数
plan_critique_disabled: false     # 关闭多轮 critique (用户自负责)
skip_impl_subagent_check: false   # true 跳过 "impl 必须经 generator Stop" 门禁 (纯绿区微改 sprint 才设)
network_in_polish: true           # polish_worker 是否允许 network

# === Fingerprint (index-updater 用于 mtime 比对) ===
fingerprint: ""
---

# Athena Project State Index (v9.9.3)

> **两层记忆 (design §5)**: Tier1 = 会话上下文/工具输出 (短命, compaction/handoff 后不权威); Tier2 = `.ai_state` (版本化持久真相)。
> 本 `_index.md` 是 **Tier2 检索路由器**, 不是第二数据库: 只存当前 path/stage/sprint、next_action、指向最新 artifact 的 pointers、精简能力位、compaction 后恢复所需的有界历史。
> 每个字段须有消费者 (hook/status/recovery/agent); 无消费者字段删或归位到拥有它的 artifact。route_confidence 详情留 route-note。
> Contract markers: **Tier1 working memory** is non-authoritative; **Tier2 persistent memory** is project truth; **_index.md retrieval router** is bounded to 10 route/current-state entries.

> 本文件由 Athena 自动维护. 不要手工修改 frontmatter 字段以外的部分除非你知道你在做什么.

## 当前状态

[由主 agent 在 stage 切换时简短追加; 只保留最新 10 条, 旧记录归 session-log/git]

## 工具调度建议

根据 `tools_available` + `platform_features`, 主 agent 进入每个 stage 时按下表选工具:

### brainstorm stage
- 主 agent 与用户对话, 不读 compound (创意空间不污染)
- 不 spawn subagent, 不 worktree

### roadmap stage
- 主 agent 调研 + 用户确认
- 输出 items.yaml + roadmap.md

### plan / design stage (强制 critique)
- 主 agent 用 ultrathink (CC) / xhigh (CX) 出 design.md 初版
- 调用 `critic` subagent (独立 context, read-only); 主 agent 将返回段落写入 design.md
- 最多 `plan_critique_max_rounds` 轮 (默认 4)
- PASS 才进 impl/design

### impl stage (subagent 始终用)
- CC: Task `generator` subagent
- CX: `spawn_agent` 启动 generator
- Refactor/System: CC 用当前 isolation 能力; CX 由主 thread 建 worktree, 任务携带绝对路径, agent 用 `pwd`/`workdir` 验证
- 并行 ≥ 2 subagent 改文件时: 强制 worktree 隔离

### review stage (2+1)
- `reviewer` + `spec-compliance` 并行返回; 主 agent 合并 passN.md 后再跑 `evaluator`
- spec-compliance 检查 design.md vs git diff (MISSING/EXTRA/DEVIATED)
- evaluator 返回 VERDICT; 主 agent 追加并更新 `_index.next_action`

### polish stage (Refactor/System 强制)
- spawn `polish_worker` (workspace-write, network=true 查最佳实践)
- 产出 cleanup-pass.md

### ship stage
- 主 agent commit + push
- Refactor/System 还需检查 architecture/ 更新 (delivery-gate)

## 历史 (由 pace-continuator hook 自动追加, 最多保留近 10 条)
