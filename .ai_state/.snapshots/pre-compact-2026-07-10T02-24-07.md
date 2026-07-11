---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.9.0 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.9.0"

# === PACE 路由状态 ===
path: "Feature"                   # Hotfix | Bugfix | Quick | Feature | Refactor | System
stage: "ship"                     # brainstorm | roadmap | plan | design | impl | runtime-verify | review | polish | ship
current_sprint_slug: ""          # 当前 sprint 目录名, 如 "2026-05-25-jwt-refresh"
current_roadmap_slug: ""  # 仅 roadmap stage 期间填
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 路由审议 (v9.9.0) ===
route_confidence: 0.8             # 0-1, 入口路由审议置信度 (主 agent 审议 Step 3 写)
route_history: ["2026-07-07 System: F1 orchestrator framework design (fullstack-delivery roadmap 首片, 档案由 quantum session 移交)"]  # re-route 记录
plan_model: ""                    # "" | "fable" — System/Refactor 的 plan/design 审议切 fable-5 (贵, opt-in)

# === 平台与版本 ===
platforms_enabled: ["both"]       # cc | cx | both
cc_version: "claude-code (unknown, desktop app 会话, CLI 不在 PATH)"
cx_version: "codex-cli 0.142.5"
ag_callable: false                # antigravity (agy) 未安装

# === 平台原生能力 (athena-init 探测) ===
platform_features:
  cc_subagent_task: true          # CC Task tool (always true)
  cc_ultrathink_supported: true   # CC v2.1.68+ ultrathink keyword
  cc_isolation_worktree: true     # 本会话 Agent tool 实测支持 isolation: worktree
  cc_subagent_stop_hook: true     # CC SubagentStop 原生事件
  cc_worktree_hooks: true         # CC WorktreeCreate/Remove 原生事件
  cc_stop_prompt_hook: true       # CC Stop hook prompt 类型 (2026-03+)
  cx_spawn_agent: true            # codex 0.142.5 >= 0.128
  cx_plan_mode_reasoning_effort: true    # codex 0.142.5 >= 0.105.0
  cx_spawn_agents_on_csv: true    # 0.142.5 且 config.toml multi_agent=true
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
  features_count: 4
  issues_count: 0
  refactors_count: 0
  systems_count: 2
  requirements_count: 1
  reviews_count: 6
  cleanup_count: 2
  compound:
    learning: 1
    trick: 0
    decision: 1
    explore: 0

# === Pointers (指向最新相关文件) ===
pointers:
  latest_design: "sprints/2026-07-08-f6-end-to-end-drill/design.md"
  latest_review: "sprints/2026-07-08-f6-end-to-end-drill/reviews/pass1.md"
  latest_cleanup: "sprints/2026-07-08-f5-biz-delivery-loop/cleanup-pass.md"
  latest_brainstorm: ""
  latest_decisions: ["compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md"]
  latest_lessons: ["compound/2026-07-08-learning-hook-order-and-worktree-counts.md"]
  latest_architecture_update: "2026-07-08T06:11:10.426746Z"
  latest_requirement: "requirements/fullstack-delivery-pack.md"

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
next_action: "roadmap_complete"  # evaluator/Stop prompt 写: runtime-verify | polish | ship | rework_impl | next_roadmap_item:{slug}
last_subagent: "reviewer"
last_subagent_at: "2026-07-08T05:14:07.007802Z"
active_worktrees: []
last_critic_round: 3              # plan stage critic 已跑轮数
design_changed_after_impl: false  # design.md 改后需 re-review

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_min_rounds: 0       # v9.9.0 (U2): 0=auto (Refactor/System=2, 其余=1); delivery-gate 在 ship 验 design.md 轮数
plan_critique_disabled: false     # 关闭多轮 critique (用户自负责)
skip_impl_subagent_check: false   # v9.9.0 (U1): true 跳过 "impl 必须经 generator" 门禁 (纯绿区微改 sprint 才设)
network_in_polish: true           # polish_worker 是否允许 network

# === Fingerprint (index-updater 用于 mtime 比对) ===
fingerprint: ""
---

# Athena Project State Index (v9.9.0)

> 本文件由 Athena 自动维护. 不要手工修改 frontmatter 字段以外的部分除非你知道你在做什么.

## 当前状态

[由主 agent 在 stage 切换时简短追加]

- `2026-07-07 12:34`: F1 进入 impl。已按 Claude design-brief 落 `design.md`, 新增 9.9.0 全栈交付 skills 骨架与 Codex 注册；下一步 runtime-verify/review。
- `2026-07-07 20:29`: F1 token-usage collector 已实现并 runtime-verify。真实 CX Stop payload 未暴露 usage, `token-usage.yaml` 记录 no_usage_found；下一步 review/critic。
- `2026-07-08 10:48`: F1 review pass1=CONCERNS。已修 SubagentStop token 收集、delivery-gate 工作区计数、reference schema；下一步 polish。
- `2026-07-08 11:05`: F1 polish 完成。已写 cleanup-pass、compound learning/decision、architecture 现状档；下一步 ship。
- `2026-07-08 11:25`: F1 roadmap 标记 completed。F2 scaffold-page-gen sprint 已进入 plan，next_action=next_roadmap_item:f2-scaffold-page-gen。
- `2026-07-08 12:18`: F2 scaffold-page-gen 首片实现完成。已新增 Convention Pack contract、quantum-front adapter、pack 校验脚本与 CC/CX 回归；review 仍待执行。
- `2026-07-08 13:05`: F2 review pass1=PASS。已补 runtime-env.md 约束、稳定 CC/CX parity 验证口径；roadmap 准备进入 F3。
- `2026-07-08 13:15`: F3 db-schema-gen/unit-test-gen 实现与验证完成。已对接 quantum-backend DB/Test Convention Pack；下一步 review。
- `2026-07-08 13:30`: F3 fallback review pass1=PASS。subagent 额度失败后按用户指令主线程自审收口；roadmap 进入 F4。
- `2026-07-08 14:02`: F4 fallback review pass1=PASS。security-test/playwright-e2e contract、quantum adapters、共享 validator 与 CC/CX parity 已完成；roadmap 进入 F5。
- `2026-07-08 14:35`: F5 biz-delivery-loop System closeout PASS。新增 loop/manifest validators、report runtime-read 字段、runtime-verify/review/polish/architecture；roadmap 进入 F6。
- `2026-07-08 14:55`: F6 static contract drill PASS。front/backend/cowork 本机测试通过, 动态 E2E blocker 已落档；fullstack-delivery roadmap complete。

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
- `2026-07-07 02:24:00`: stage=plan sprint=2026-07-07-f1-orchestrator-framework-design turn-end
- `2026-07-07 01:53:39`: stage=  sprint=  turn-end
