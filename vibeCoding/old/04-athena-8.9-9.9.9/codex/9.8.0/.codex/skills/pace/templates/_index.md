---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.8.0 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.8.0"

# === PACE 路由状态 ===
path: ""                          # Hotfix | Bugfix | Quick | Feature | Refactor | System
stage: ""                         # brainstorm | roadmap | plan | design | impl | runtime-verify | review | polish | ship
current_sprint_slug: ""           # 当前 sprint 目录名, 如 "2026-05-25-jwt-refresh"
current_roadmap_slug: ""          # 仅 roadmap stage 期间填
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 平台与版本 ===
platforms_enabled: ["cc"]         # cc | cx | both
cc_version: ""                    # 由 athena-init 探测
cx_version: ""
ag_callable: false                # antigravity (agy) 可调度?

# === 平台原生能力 (athena-init 探测) ===
platform_features:
  cc_subagent_task: true          # CC Task tool (always true)
  cc_ultrathink_supported: false  # CC v2.1.68+ ultrathink keyword
  cc_isolation_worktree: false    # CC v2.x+ subagent frontmatter isolation: worktree
  cc_subagent_stop_hook: false    # CC SubagentStop 原生事件
  cc_worktree_hooks: false        # CC WorktreeCreate/Remove 原生事件
  cc_stop_prompt_hook: false      # CC Stop hook prompt 类型 (2026-03+)
  cx_spawn_agent: false           # Codex spawn_agent (0.128+)
  cx_plan_mode_reasoning_effort: false   # Codex 0.105.0+ plan_mode_reasoning_effort
  cx_spawn_agents_on_csv: false   # 实验性
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

# === 进度计数 (index-updater hook 自动维护, 不手填) ===
counts:
  features_count: 0               # sprints/ 下 path=Feature 目录数
  issues_count: 0                 # path=Bugfix 目录数
  refactors_count: 0              # path=Refactor 目录数
  systems_count: 0                # path=System 目录数
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
  latest_architecture_update: ""  # architecture/ARCHITECTURE.md mtime

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
next_action: ""                   # evaluator/Stop prompt 写: runtime-verify | polish | ship | rework_impl | next_roadmap_item:{slug}
last_subagent: ""                 # SubagentStop hook 写
last_subagent_at: ""
active_worktrees: []              # WorktreeCreate/Remove hook 维护
last_critic_round: 0              # plan stage critic 已跑轮数
design_changed_after_impl: false  # design.md 改后需 re-review

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_disabled: false     # 关闭多轮 critique (用户自负责)
network_in_polish: true           # polish_worker 是否允许 network

# === Fingerprint (index-updater 用于 mtime 比对) ===
fingerprint: ""
---

# Athena Project State Index (v9.8.0)

> 本文件由 Athena 自动维护. 不要手工修改 frontmatter 字段以外的部分除非你知道你在做什么.

## 当前状态

[由主 agent 在 stage 切换时简短追加]

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
- spawn `critic` subagent (独立 context, read-only)
- 最多 `plan_critique_max_rounds` 轮 (默认 4)
- PASS 才进 impl/design

### impl stage (subagent 始终用)
- CC: Task `generator` subagent
- CX: spawn_agent `generator.toml`
- Refactor/System: 强制 `isolation: worktree` (CC) 或 `git worktree add + --cwd` (CX)
- 并行 ≥ 2 subagent 改文件时: 强制 worktree 隔离

### review stage (3 subagent 并行)
- `reviewer` + `spec-compliance` + `evaluator` 同时跑
- spec-compliance 检查 design.md vs git diff (MISSING/EXTRA/DEVIATED)
- evaluator 给 VERDICT (PASS/CONCERNS/REWORK/FAIL) 写入 _index.next_action

### polish stage (Refactor/System 强制)
- spawn `polish_worker` (workspace-write, network=true 查最佳实践)
- 产出 cleanup-pass.md

### ship stage
- 主 agent commit + push
- Refactor/System 还需检查 architecture/ 更新 (delivery-gate)

## 历史 (由 pace-continuator hook 自动追加, 最多保留近 10 条)
