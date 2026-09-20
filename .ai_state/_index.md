---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.9.8 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.9.9"

# === PACE 路由状态 ===
path: "System"
stage: "review"
breadcrumb: "on"                # v9.9.6 每轮 stage 面包屑注入; "off" 关闭 (fail-open)
current_sprint_slug: "2026-09-20-heredoc-aware-shell-guard"
current_roadmap_slug: "q12-batch2-production-gaps"
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 路由审议 (v9.9.6) ===
route_confidence: 0.97  # 切片7+8 并行设计流水线; 双侦察逐行核实; 写集互斥, generator 窗口错开
route_history: ["2026-09-20 System/design: q12 slice7+8 并行流水线; Q12#12 + Q12#14+切片2遗留; conf=0.97", "2026-09-20 System/design: q12 slice4 contract-parser-diagnostics; Q12#5/#7/#8 + 字节断言接管; conf=0.98", "2026-09-20 System/design: q12 slice3 review-binding-preflight; Q12#6/#9/#10; conf=0.99", "2026-09-20 System/design takeover: CC 接管 codex slice2 evidence-pipeline; 采纳 pipefail 设计; conf=0.98", "2026-09-20 System/roadmap: Q12 batch2 production gaps; 15 actionable, 2 no-change, 1 external; conf=0.99", "2026-09-16 Quick: CC local 7-agent maxTurns 70→90; exact scope; conf=1.0", "2026-09-14 Hotfix: apply pending 9.9.9 CC/CX patches; preserve chats; conf=0.99", "2026-07-28 System impl 范围扩张 →index-overflow.md#rh-0", "2026-07-28 System impl 红区降级 →index-overflow.md#rh-1", "2026-07-29 System impl 安装态同步 →index-overflow.md#rh-2"]  # re-route ≤10, item ≤160B
plan_model: "opus"              # 2026-09-20: fable 触发额度上限, System plan/design 审议改 opus

# === 平台与版本 ===
platforms_enabled: ["both"]       # cc | cx | both
cc_version: "claude-code 2.1.236"
cx_version: "codex-cli 0.153.4"
ag_callable: false                # antigravity (agy) 未安装

# === 平台原生能力 (athena-init 探测) ===
platform_features:
  cc_subagent_task: true          # 共享字段名保留; CC 当前 Agent tool 可用
  cc_ultrathink_supported: true   # CC v2.1.68+ ultrathink keyword
  cc_isolation_worktree: true     # CC v2.x+ subagent frontmatter isolation: worktree
  cc_subagent_stop_hook: true     # CC SubagentStop 原生事件
  cc_worktree_hooks: true         # CC WorktreeCreate/Remove 原生事件
  cc_stop_prompt_hook: true       # CC Stop hook prompt 类型 (2026-03+)
  cx_spawn_agent: true            # Codex 0.145.0+ native multi-agent v2
  cx_plan_mode_reasoning_effort: true    # Codex 0.105.0+ plan_mode_reasoning_effort
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
  vm_available: true              # 2026-09-06 配置+SSH只读验证；项目场景未验证

# === 进度计数 (index-updater hook 自动维护, 不手填) ===
# 9.9.8 AC9: archive 默认不被扫描 → 本节只反映热层, 不是项目累计值。
# 归档前累计值留档于 sprints/2026-08-27-athena-9-9-8/index-overflow.md#st-11
counts:
  features_count: 1
  issues_count: 0
  refactors_count: 0
  systems_count: 8
  requirements_count: 1
  reviews_count: 21
  cleanup_count: 6
  compound:
    learning: 7
    trick: 0
    decision: 5
    explore: 2

# === Pointers (指向最新相关文件) ===
pointers:
  latest_design: "sprints/2026-09-20-runtime-secret-false-positive/design.md"
  latest_review: "sprints/2026-09-20-review-binding-preflight/reviews/implementation-review.md"
  latest_cleanup: "sprints/2026-09-20-runtime-secret-false-positive/cleanup-pass.md"
  latest_brainstorm: "sprints/2026-09-06-athena-next-version/brainstorm.md"
  latest_decisions: ["compound/2026-08-27-decision-retire-local-telemetry-collection.md", "compound/2026-07-28-decision-close-prompt-engineering-direction.md", "compound/2026-07-13-decision-quantum-7-to-2-consolidation.md", "compound/2026-07-13-decision-index-field-audit.md", "compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md"]
  latest_lessons: ["compound/2026-09-20-learning-single-source-error-strings.md", "compound/2026-09-20-learning-self-mutating-regression-test.md", "compound/2026-07-28-learning-reserved-ac-labels-silent-exemption.md", "compound/2026-07-14-learning-canonical-install-path-runtime.md", "compound/2026-07-11-learning-worktree-generator-ledger-gap.md"]
  latest_architecture_update: "2026-09-20T12:17:35.309Z"
  latest_requirement: "requirements/fullstack-delivery-pack.md"

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
# 9.9.8: await-review-result = 已发起一次原生异步 review, 结果在后续 turn 到达;
# 该值期间 Stop / pace-continuator 放行不注入续跑 (等待不烧 token), 完成通知轮落盘后清空。
next_action: "await-review-result"
last_subagent: "polish-worker"
last_subagent_at: "2026-09-20T04:11:57Z"
active_worktrees: []
harness_target_outside_repo: false
last_critic_round: 0              # 9.9.8: 设计作者不自审, critic 为 stub
design_changed_after_impl: true

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_min_rounds: 0       # 9.9.8: 作者会话 0 轮; 独立挑战走派生 review-packet
plan_critique_disabled: false     # 关闭多轮 critique (用户自负责)
skip_impl_subagent_check: false
network_in_polish: true           # polish_worker 是否允许 network

# === Fingerprint (index-updater 用于 mtime 比对) ===
fingerprint: ""
---

# Athena Project State Index (v9.9.8)

> **三层记忆 (9.9.8 design «`ai_state`：热状态、耐久知识、冷历史»)**: 热状态 = `_index.md` + 当前 sprint (每轮只读 `_index`, 再跟 pointer); 耐久知识 = `requirements/`/`architecture/`/`compound/` (命中才读); 冷历史 = `sprints/archive/{YYYY}/{slug}` (默认排除, 按 slug 显式查); telemetry = `.runtime/` (Git ignored, 不进上下文)。
> 本 `_index.md` 是 **Tier2 检索路由器**, 不是第二数据库: 只存当前 path/stage/sprint、next_action、指向最新 artifact 的 pointers、精简能力位、compaction 后恢复所需的有界历史。
> 每个字段须有消费者 (hook/status/recovery/agent); 无消费者字段删或归位到拥有它的 artifact。route_confidence 详情留 route-note。
> Contract markers: **Tier1 working memory** is non-authoritative; **Tier2 persistent memory** is project truth; **_index.md retrieval router** is bounded to ≤12 KiB, 10 route/current-state entries, 160 bytes per entry.

> 本文件由 Athena 自动维护. 不要手工修改 frontmatter 字段以外的部分除非你知道你在做什么.

## 当前状态

- 2026-09-06 VM: SSH可达RHEL10.2；仅证明传输，项目服务待验证。
- Previous status and shifted route →index-overflow.md#previous-current-state
- older 当前状态 →index-overflow.md#st-0
- older 当前状态 →index-overflow.md#st-0
- older 当前状态 →index-overflow.md#st-1
- older 当前状态 →index-overflow.md#st-0
- older 当前状态 →index-overflow.md#st-0
- older 当前状态 →index-overflow.md#st-1
- older 当前状态 →index-overflow.md#st-2
- older 当前状态 →.ai_state/index-overflow.md#st-1



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
- CX: `spawn_agent` 启动 generator
- Refactor/System: CC 用当前 isolation 能力; CX 由主 thread 建 worktree, 任务携带绝对路径, agent 用 `pwd`/`workdir` 验证
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

<!-- 2026-07-28 W29: ## 历史 段已废除 — 历史归 route_history 与 git log; 原七条 turn-end 记录存档于 sprints/2026-08-27-athena-9-9-8/index-overflow.md#hi-0 -->
