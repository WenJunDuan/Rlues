---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.9.3 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.9.3"

# === PACE 路由状态 ===
path: "System"                 # 9.9.8 review contract + hook austerity + future verifier slots
stage: "design"                # Grok/Codex 已完善 design；等待独立 Claude 执行派生 packet（作者不自审）
current_sprint_slug: "2026-08-27-athena-9-9-8"
current_roadmap_slug: "athena-9-9-8"
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 路由审议 (v9.9.0) ===
route_confidence: 0.94             # 用户显式开 9.9.8 System；三切片 roadmap；独立 Claude 复盘但设计作者不自审
route_history: ["2026-07-10 System: CC 9.9.1 redesign from CC 9.9.0 baseline, awaiting Fable5 review", "2026-07-10 System: user-approved impl-first flow; Fable5 post-implementation review remains mandatory", "2026-07-13 System: user-approved Athena 9.9.2 overall architecture upgrade; four primitives + spec-gate + two-tier memory are mandatory", "2026-07-14 System: repair Athena 9.9.3 review findings, full regression, formal review, merge and publish", "2026-07-25 System+roadmap: research-led Athena 9.9.6 prompt architecture refresh for Claude Code and Codex", "2026-07-25 System impl: user authorized Claude review repairs directly in main checkout without worktree", "2026-07-28 System impl 范围扩张 (非 re-route): 用户拍板把 2026-07-27-hotfix-gate-contract 的 A-E 五条并入本 sprint 作追加范围, 不另立 sprint; path 维持 System (design 原建议 Feature 作废); 改动对象含 ~/.claude 与 ~/.codex 安装态, 依 stages.md 先例不用 worktree", "2026-07-28 System impl 红区降级 (用户显式批准): spawn generator 执行 G1-G5 被 subagent-worktree-check.cjs 无条件 block (P9 二次撞上, 无豁免出口); worktree 对 repo 外的 ~/.claude|~/.codex 零隔离却照样阻断写入, 任务结构性死锁。用户批准主 agent 直做 G1-G5, 改安装态前已逐个备份 (12 文件, pre-g1g5-20260728T024943Z)", "2026-07-29 System impl: 用户授权 hotfix2 W35-W40 安装态同步、真实 sprint 采数、validator 收口与 main 推送；canonical release 优先于过时 _hf2_sync 快照", "2026-08-27 System: Athena 9.9.8 Thin PACE Control Plane；一次原生 review、hook 红黄绿、有界 ai_state；VM/LaaV 仅保留 opt-in 接口；独立 Claude 按 packet 复盘"]  # re-route 记录 (≤10)
plan_model: "fable"                    # "" | "fable" — System/Refactor 的 plan/design 审议切 fable-5 (贵, opt-in)

# === 平台与版本 ===
platforms_enabled: ["both"]       # cc | cx | both
cc_version: "claude-code 2.1.211"
cx_version: "codex-cli 0.145.0"
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
  reviews_count: 18
  cleanup_count: 7
  compound:
    learning: 5
    trick: 0
    decision: 4
    explore: 1

# === Pointers (指向最新相关文件) ===
pointers:
  latest_design: "sprints/2026-08-27-athena-9-9-8/design.md"
  latest_review: "sprints/2026-07-29-athena-9-9-6-hotfix2/reviews/pass1.md"
  latest_cleanup: "sprints/2026-07-29-athena-9-9-6-hotfix2/cleanup-pass.md"
  latest_brainstorm: ""
  latest_decisions: ["compound/2026-07-28-decision-close-prompt-engineering-direction.md", "compound/2026-07-13-decision-quantum-7-to-2-consolidation.md", "compound/2026-07-13-decision-index-field-audit.md", "compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md"]
  latest_lessons: ["compound/2026-07-28-learning-reserved-ac-labels-silent-exemption.md", "compound/2026-07-14-learning-canonical-install-path-runtime.md", "compound/2026-07-11-learning-worktree-generator-ledger-gap.md", "compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md", "compound/2026-07-08-learning-hook-order-and-worktree-counts.md"]
  latest_architecture_update: "2026-07-29T14:20:24.017Z"
  latest_requirement: "requirements/fullstack-delivery-pack.md"

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
next_action: "Independent Claude executes review-packet.md and writes reviews/design-review.md; implementation remains unauthorized"
last_subagent: "athena_998_architecture_challenge"
last_subagent_at: "2026-08-27T02:57:33.966970Z"
active_worktrees: []
last_critic_round: 0              # 9.9.8：设计作者不自审
design_changed_after_impl: false

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_min_rounds: 0       # 9.9.8：作者会话 0 轮；独立审查走 review-packet
plan_critique_disabled: true      # 本 sprint 用户要求：写设计的模型不审自己的设计
skip_impl_subagent_check: false   # 当前 System sprint 尚未授权 impl；后续 writer 仍按门禁绑定
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

- 2026-08-27 design：Grok/Codex 已完善 `Thin PACE Control Plane`：一次原生 review、hook 红黄绿（现场复现无害 `rg` parser 误判）、final-diff hash、有界 `_index`。双端 `athena-vm` 已具 setup/doctor，当前未配置；LaaV 仅作 logprob best-of-N/进度实验，不替代 VM/test/review/ship。packet 52 行并绑定最新 design hash；下一步仍是独立 Claude 复盘，通过前不授权实现。
- 2026-07-29 ship：hotfix2 已完成提交并推送 `main`（`19dd8d5`）；delivery-gate exit 0，工作树干净，当前 sprint/roadmap 项均 completed。AC9 A/B N≥3 仍按范围锁定为下一 sprint，不影响本轮交付完成。
- 2026-07-29 W35-W40 hotfix2：canonical 双端包已同步 ~/.claude 与 ~/.codex（30 个目标，逐文件事务备份）；历史/会话/SQLite 保留，缓存清理完成，_to_delete 内容可恢复隔离。validator 66/0/0、W35-W40 台账、真实 sprint `verdict_ac2=PASS`（git 度量代理）、review/evaluator PASS；AC9 A/B N≥3 明确 deferred 到下一 sprint。
- 2026-07-28 W31-W34 安装态部署已完成：12 个源条目、10 个唯一目标，9 个过期目标更新；两端哈希、语法、历史与 SQLite 校验通过。会话、历史、配置、认证、插件、项目态和数据库保留；两个仓库 _to_delete_* 目录移入保留备份隔离区并从仓库移除。记录见 sprints/2026-07-28-installation-sync-w31-w34/deployment.md。
- 2026-07-28 用户主动关闭 9.9.6 prompt-engineering / gate-descaling 方向：原本的改动反复且叙述冗长，后续不再考虑同类扩展。活动 sprint、roadmap 与续跑动作已清空；已完成实现、同步、验证和历史记录保留，未执行项标为 superseded，不伪称 release 已完成。决策档案见 compound/2026-07-28-decision-close-prompt-engineering-direction.md。
- `2026-07-28`: **10bd534 gate-descaling 本地 draft 已同步到当前系统端点**：CC 128 / CX 33 / shared skills 97，管理哈希 257/257；历史 JSONL 2 份共 545 行、SQLite 9 个 quick-check=ok；只清理两端 `.DS_Store` 与 `__pycache__`（1,116 文件 / 16,467,927 字节），未触碰历史、会话、插件、数据库、认证或活动缓存。静态验证 `66 PASS / 0 FAIL / 0 SKIP`。仍为 `impl` / `reviewable draft`，未标记 release complete。详见 `sprints/2026-07-25-athena-9-9-6-prompt-engineering/deployments/20260728T061441Z-gate-descaling-sync.md`。
- `2026-07-28`: **hotfix gate-contract 并入本 sprint 作追加范围**（用户拍板，不另立 sprint）。核出现场踩雷：本 sprint `design.md:316-317` 的 AC11/AC12 是**业务 AC 却占了 harness 保留元标号** —— `delivery-gate.cjs:813` 把 AC11/AC12 排除在 per-AC 证据绑定之外，即"本地测试树全覆盖"与"A/B eval N≥3 Pareto"两条 ship 时静默免检；`validateMetaAcceptance` 反而据标号额外要求 evaluator PASS + cleanup 完成 + 活动 worktree=1（碰巧与 System 真义务重合，未炸）。这正是 hotfix design §一 失败 #3 的现场复现。ship 契约缺口实测：`evidence.yaml` 2 条记录 / 绑定字段命中 **0**，`review-manifest.yaml`、`tdd-evidence.yaml`、`cleanup-pass.md`、`reviews/` 全缺；critic 字面轮次 5（System 地板 2，已过，但新增范围需再加一轮）；活动 worktree=1。新 design 的 AC 段已实测可被 spec-gate 解析（/tmp fixture 喂 PreToolUse，exit 0）。
- `2026-07-25`: **Claude review 成立项已修复，仍处 impl**：P0 provider/background/spawn gate、validator、hook/docs/security drift 收口；local-only validator 63 PASS / 0 FAIL / 0 SKIP（含 fresh setup、exact Codex 0.145 config.load、F-series、worktree gate fixtures）。用户明确要求直接在 main checkout 修改；三种 subagent 角色均因无 shell/编辑工具零写入失败，主 thread 接管。完整 F1-F6/runtime-verify/正式 2+1 review 仍 pending，未 commit/push/release。证据见 `review-repair-evidence.md`。
- `2026-07-25`: **用户最终确认 CC 角色矩阵**：main `model=best`；无全局 subagent override；architect/critic=Fable，evaluator 与其余四个实现/审查角色=Opus；effort 保持 3×xhigh + 4×high。
- `2026-07-25`: **9.9.6 reviewable bottom draft 已收敛到当前 Rlues/main 工作目录**（uncommitted；临时 worktree/branch 已删除）。CC 117 / CX 115 文件，26 skills/端；Codex 0.145.0 实际加载配置成功；9.9.3 零 diff；本地 tests/evals 尚未创建，F1-F7 保持 pending。证据见当前 sprint `bottom-draft-evidence.md`。

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
- `2026-07-25 17:56:21`: stage=impl sprint=2026-07-25-athena-9-9-6-prompt-engineering turn-end
- `2026-07-21 03:21:03`: stage=  sprint=  turn-end
- `2026-07-21 03:18:58`: stage=  sprint=  turn-end
- `2026-07-11 12:59:01`: stage=ship sprint=2026-07-10-claude-code-9-9-1-impl turn-end
- `2026-07-10 13:31:06`: stage=review sprint=2026-07-10-claude-code-9-9-1-impl turn-end
- `2026-07-07 02:24:00`: stage=plan sprint=2026-07-07-f1-orchestrator-framework-design turn-end
- `2026-07-07 01:53:39`: stage=  sprint=  turn-end
