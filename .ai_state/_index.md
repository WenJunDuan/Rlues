---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.9.8 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.9.8"

# === PACE 路由状态 ===
path: "Hotfix"
stage: "ship"
breadcrumb: "on"                # v9.9.6 每轮 stage 面包屑注入; "off" 关闭 (fail-open)
current_sprint_slug: "2026-09-07-pace-task-triage-hotfix"
current_roadmap_slug: ""
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 路由审议 (v9.9.6) ===
route_confidence: 1.0  # 用户授权自然语言分诊 Hotfix；父 System 恢复事实留在原日志
route_history: ["2026-07-25 System+roadmap: research-led Athena 9.9.6 prompt architecture refresh for Claude Code and Codex", "2026-07-25 System impl: user authorized Claude review repairs directly in main checkout without worktree", "2026-07-28 System impl 范围扩张 (非 re-route): 用户拍板把 2026-07-27-hotfix-gate-contract 的 A-E 五条并入本 sprint 作 →index-overflow.md#rh-0", "2026-07-28 System impl 红区降级 (用户显式批准): spawn generator 执行 G1-G5 被 subagent-worktree-check.cjs 无条件 block →index-overflow.md#rh-1", "2026-07-29 System impl: 用户授权 hotfix2 W35-W40 安装态同步、真实 sprint 采数、validator 收口与 main 推送；canoni →index-overflow.md#rh-2", "2026-08-27 System: Athena 9.9.8 Thin PACE Control Plane；一次原生 review、hook 红黄绿、有界 ai_state；VM/LaaV 仅保留 o →index-overflow.md#rh-3", "2026-09-06 System/brainstorm: CC/CX next release; efficiency, parallel and fullstack; proposal only; conf=0.96", "2026-09-06 System/design: 9.9.9; PACE+state; single-platform base; 3 goals; design reviewed; impl pending; conf=0.98", "2026-09-07 System audit: Grok aeb1da6; standalone assets pass, contract/code gaps reproduced; no install; conf=0.99", "2026-09-07 Hotfix: natural-language triage + state-repair gate; parent saved in session-log; conf=1.0"]  # re-route ≤10, item ≤160B
plan_model: "fable"               # "" | "fable" — System/Refactor 的 plan/design 审议切 fable-5 (贵, opt-in)

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
  features_count: 0
  issues_count: 0
  refactors_count: 0
  systems_count: 2
  requirements_count: 1
  reviews_count: 10
  cleanup_count: 1
  compound:
    learning: 5
    trick: 0
    decision: 5
    explore: 2

# === Pointers (指向最新相关文件) ===
pointers:
  latest_design: ""
  latest_review: ""
  latest_cleanup: ""
  latest_brainstorm: "sprints/2026-09-06-athena-next-version/brainstorm.md"
  latest_decisions: ["compound/2026-08-27-decision-retire-local-telemetry-collection.md", "compound/2026-07-28-decision-close-prompt-engineering-direction.md", "compound/2026-07-13-decision-index-field-audit.md", "compound/2026-07-13-decision-quantum-7-to-2-consolidation.md", "compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md"]
  latest_lessons: ["compound/2026-07-28-learning-reserved-ac-labels-silent-exemption.md", "compound/2026-07-14-learning-canonical-install-path-runtime.md", "compound/2026-07-11-learning-worktree-generator-ledger-gap.md", "compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md", "compound/2026-07-08-learning-hook-order-and-worktree-counts.md"]
  latest_architecture_update: "2026-08-27T19:26:23+08:00"
  latest_requirement: "requirements/fullstack-delivery-pack.md"

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
# 9.9.8: await-review-result = 已发起一次原生异步 review, 结果在后续 turn 到达;
# 该值期间 Stop / pace-continuator 放行不注入续跑 (等待不烧 token), 完成通知轮落盘后清空。
next_action: ""
last_subagent: "athena999_design_review_followup"
last_subagent_at: "2026-09-06T10:29:17.861980+00:00"
active_worktrees: []  # 已于 2026-09-07 移除过期 athena-9.9.9-design worktree；保留其分支作回退锚点
harness_target_outside_repo: true  # 安装目标在 ~/.claude ~/.codex ~/.agents；单写者逐文件备份，仓库源码同步
last_critic_round: 0              # 9.9.8: 设计作者不自审, critic 为 stub
design_changed_after_impl: false

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_min_rounds: 0       # 9.9.8: 作者会话 0 轮; 独立挑战走派生 review-packet
plan_critique_disabled: false     # 关闭多轮 critique (用户自负责)
skip_impl_subagent_check: false   # true 跳过 "impl 必须经 generator Stop" 门禁 (纯绿区微改 sprint 才设)
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

- 2026-09-07 Hotfix: task triage installed; validator 60/0; parent System recovery preserved in session-log.
- 2026-09-07 Hotfix: gate quickref + agent 70-turn policy installed; parent System pending. See session-log.
- 2026-09-07 audit: 首装资产通过；核心缺陷仍在，见latest_review；不安装。
- 2026-09-07 impl: 已合入审查绑定/init 并发/Gradle 分类/LaaV 评分修复；validator 58 PASS；未安装。
- 2026-09-07 impl: 9.9.9 候选包已核对补全（无 maxTurns、REVIEW 进 skill、LaaV opt-in、VM json 入包）；未安装；待 Claude 审核。
- 2026-09-06 design: 用户授权生成CC/CX 9.9.9候选包；设计已复核，进入实现。
- 2026-09-06 VM: SSH可达RHEL10.2；仅证明传输，项目服务待验证。
- Previous status and shifted route →index-overflow.md#previous-current-state


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
