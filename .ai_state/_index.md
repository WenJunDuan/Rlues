---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.9.3 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.9.3"

# === PACE 路由状态 ===
path: ""                        # idle: 9.9.3 release_complete, 无进行中 sprint (P8 idle 态)
stage: ""                        # idle
current_sprint_slug: ""          # 上一 sprint: 2026-07-14-athena-9-9-3-review-fixes (expedited ship)
current_roadmap_slug: ""  # 仅 roadmap stage 期间填
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 路由审议 (v9.9.0) ===
route_confidence: 0.99             # 0-1, 入口路由审议置信度 (主 agent 审议 Step 3 写)
route_history: ["2026-07-07 System: F1 orchestrator framework design (fullstack-delivery roadmap 首片, 档案由 quantum session 移交)", "2026-07-10 System: Athena 9.9.1 compatibility release from 9.9.0 baseline", "2026-07-10 System: CC 9.9.1 redesign from CC 9.9.0 baseline, awaiting Fable5 review", "2026-07-10 System: user approved impl-first flow; Fable5 post-implementation review remains mandatory", "2026-07-13 System: user-approved Athena 9.9.2 overall architecture upgrade; four primitives + spec-gate + two-tier memory are mandatory", "2026-07-14 System: repair Athena 9.9.3 review findings, full regression, formal review, merge and publish"]  # re-route 记录
plan_model: "fable"                    # "" | "fable" — System/Refactor 的 plan/design 审议切 fable-5 (贵, opt-in)

# === 平台与版本 ===
platforms_enabled: ["both"]       # cc | cx | both
cc_version: "claude-code (unknown, desktop app 会话, CLI 不在 PATH)"
cx_version: "codex-cli 0.144.1"
ag_callable: false                # antigravity (agy) 未安装

# === 平台原生能力 (athena-init 探测) ===
platform_features:
  cc_subagent_task: true          # CC Task tool (always true)
  cc_ultrathink_supported: true   # CC v2.1.68+ ultrathink keyword
  cc_isolation_worktree: true     # 本会话 Agent tool 实测支持 isolation: worktree
  cc_subagent_stop_hook: true     # CC SubagentStop 原生事件
  cc_worktree_hooks: true         # CC WorktreeCreate/Remove 原生事件
  cc_stop_prompt_hook: true       # CC Stop hook prompt 类型 (2026-03+)
  cx_spawn_agent: true            # Codex 0.144.1 native multi-agent v2
  cx_plan_mode_reasoning_effort: true    # Codex 0.144.1
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
  systems_count: 8
  requirements_count: 1
  reviews_count: 17
  cleanup_count: 6
  compound:
    learning: 4
    trick: 0
    decision: 3
    explore: 0

# === Pointers (指向最新相关文件) ===
pointers:
  latest_design: "sprints/2026-07-14-athena-9-9-3-review-fixes/design.md"
  latest_review: "sprints/2026-07-14-athena-9-9-3-review-fixes/reviews/pass1.md"
  latest_cleanup: "sprints/2026-07-14-athena-9-9-3-review-fixes/cleanup-pass.md"
  latest_brainstorm: ""
  latest_decisions: ["compound/2026-07-13-decision-quantum-7-to-2-consolidation.md", "compound/2026-07-13-decision-index-field-audit.md", "compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md"]
  latest_lessons: ["compound/2026-07-14-learning-canonical-install-path-runtime.md", "compound/2026-07-11-learning-worktree-generator-ledger-gap.md", "compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md", "compound/2026-07-08-learning-hook-order-and-worktree-counts.md"]
  latest_architecture_update: "2026-07-14T05:45:11.915Z"
  latest_requirement: "requirements/fullstack-delivery-pack.md"

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
next_action: "release_complete"  # 9.9.3 verified and user-directed expedited ship
last_subagent: "generator"
last_subagent_at: "2026-07-10T08:53:02.056859Z"
active_worktrees: []
last_critic_round: 2              # 当前 sprint critic 轮次
design_changed_after_impl: false  # 4b67f82 按最终 design/pass3 findings 完成；之后未再改设计

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_min_rounds: 0       # v9.9.0 (U2): 0=auto (Refactor/System=2, 其余=1); delivery-gate 在 ship 验 design.md 轮数
plan_critique_disabled: false     # 关闭多轮 critique (用户自负责)
skip_impl_subagent_check: false   # sprint 收尾后恢复默认门禁
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

- `2026-07-14`: **9.9.3 发布收口** (`b88f615`)。review-fixes 修 6 项 finding (CX breadcrumb canonical 路径 / evaluator over-eng 语义 / M5 双端产物 / validator 基线 / 行数预算 / 发布卫生)；CX 67/67、CC 107/107、validator 223/223；pass1=PASS，2+1 闭环 (Claude 构建 → Codex 审修 → Claude 复核)。
- `2026-07-14`: housekeeping — 删 9.9.1 harness 三件 + fixtures (N-1 保留策略)；清 15 个已 ship sprint 的 token-usage.yaml/tool-trace.jsonl 遥测 (5.6M→672K, git 历史可回溯)；_index schema 标识刷 9.9.3。
- `2026-07-14`: pass3 阻塞修复已合入 main (`4b67f82`)；临时 worktree/分支已清理。用户明确要求不再跑测试并直接发布；保留已有验证证据，不声称新增 post-fix validator PASS。
- `2026-07-14`: 9.9.2 pass2 rework 已合入 main (`3e2e7f8`)；宿主 validator 206/0/0、CX 57/57、CC 101/0/0，进入 pass3。
- `2026-07-13`: pass2=REWORK；阻塞为逐 AC evidence fail-open、AC7 consumer 不完整、critic round/RELEASE/迁移指引问题。
- `2026-07-13`: pass1=REWORK；validator 123/10，provider/spec-gate/回归/证据链存在 P0。
- `2026-07-13`: 用户确认 9.9.2 是整体 System 升级，四原语、spec-gate、两层记忆、quantum 7→2 均为强制范围。
- `2026-07-11`: CC 9.9.1 pass3=PASS 并发布，worktree/branch 清理完成。
- `2026-07-11`: CC 9.9.1 Fable5 rework 完成，144/0、72/0/0、migration 11/11。
- `2026-07-10`: Athena 9.9.1 发布完成，main 推送且 roadmap 4/4 complete。

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
- CX: native `spawn_agent({task_name,message})`; 先按 `~/.agents/skills/pace/references/orchestration.md` 完成 raw Start → assignment 握手
- Refactor/System: CC 使用平台 isolation；CX 由主线程 `git worktree add`，任务携带绝对路径，agent 验证 `pwd/workdir`
- 并行 ≥ 2 subagent 改文件时: 强制 worktree 隔离

### review stage (2 + 1)
- `reviewer` + `spec-compliance` 并行返回
- 主线程合并 `passN.md` 后再启动 `evaluator`
- spec-compliance 检查 design.md vs git diff (MISSING/EXTRA/DEVIATED)
- evaluator 给 VERDICT (PASS/CONCERNS/REWORK/FAIL) 写入 _index.next_action

### polish stage (Refactor/System 强制)
- spawn `polish_worker` (workspace-write, network=true 查最佳实践)
- 产出 cleanup-pass.md

### ship stage
- 主 agent commit + push
- Refactor/System 还需检查 architecture/ 更新 (delivery-gate)

## 历史 (由 pace-continuator hook 自动追加, 最多保留近 10 条)
- `2026-07-11 12:59:01`: stage=ship sprint=2026-07-10-claude-code-9-9-1-impl turn-end
- `2026-07-10 13:31:06`: stage=review sprint=2026-07-10-claude-code-9-9-1-impl turn-end
- `2026-07-07 02:24:00`: stage=plan sprint=2026-07-07-f1-orchestrator-framework-design turn-end
- `2026-07-07 01:53:39`: stage=  sprint=  turn-end
