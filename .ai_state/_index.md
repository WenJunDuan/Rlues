---
# Athena PACE 项目状态 (.ai_state/_index.md)
# v9.9.0 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.9.0"

# === PACE 路由状态 ===
path: "System"                   # Hotfix | Bugfix | Quick | Feature | Refactor | System
stage: "ship"                     # brainstorm | roadmap | plan | design | impl | runtime-verify | review | polish | ship
current_sprint_slug: "2026-07-10-claude-code-9-9-1-impl"          # 当前 sprint 目录名, 如 "2026-05-25-jwt-refresh"
current_roadmap_slug: ""  # 仅 roadmap stage 期间填
skip_polish: false                # 项目级 opt-out (默认 false)
skip_architecture_check: false    # System/Refactor ship 前是否跳过 architecture 更新检查
skip_runtime_verify: false        # v9.8.0: true 跳过运行时验证 (纯库/无运行环境才设; System/Refactor 不建议)

# === 路由审议 (v9.9.0) ===
route_confidence: 0.99             # 0-1, 入口路由审议置信度 (主 agent 审议 Step 3 写)
route_history: ["2026-07-07 System: F1 orchestrator framework design (fullstack-delivery roadmap 首片, 档案由 quantum session 移交)", "2026-07-10 System: Athena 9.9.1 compatibility release from 9.9.0 baseline", "2026-07-10 System: CC 9.9.1 redesign from CC 9.9.0 baseline, awaiting Fable5 review", "2026-07-10 System: user approved impl-first flow; Fable5 post-implementation review remains mandatory"]  # re-route 记录
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
  systems_count: 7
  requirements_count: 1
  reviews_count: 12
  cleanup_count: 4
  compound:
    learning: 3
    trick: 0
    decision: 1
    explore: 0

# === Pointers (指向最新相关文件) ===
pointers:
  latest_design: "sprints/2026-07-10-claude-code-9-9-1-design/design.md"
  latest_review: "sprints/2026-07-10-claude-code-9-9-1-impl/reviews/pass3.md"
  latest_cleanup: "sprints/2026-07-10-claude-code-9-9-1-impl/cleanup-pass.md"
  latest_brainstorm: ""
  latest_decisions: ["compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md"]
  latest_lessons: ["compound/2026-07-11-learning-worktree-generator-ledger-gap.md", "compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md", "compound/2026-07-08-learning-hook-order-and-worktree-counts.md"]
  latest_architecture_update: "2026-07-11T01:00:45.666694Z"
  latest_requirement: "requirements/fullstack-delivery-pack.md"

# === PACE 联动字段 (v9.8.0 新, hook 自动维护) ===
next_action: ""  # CC 9.9.1 已发布 (25d4883 pushed to main); roadmap 6/6 complete; worktree/branch 已清理
last_subagent: "generator"
last_subagent_at: "2026-07-10T08:53:02.056859Z"
active_worktrees: []
last_critic_round: 3              # plan stage critic 已跑轮数
design_changed_after_impl: false  # §18 决策改动已由 pass3 重审 (2026-07-11)

# === 用户偏好 ===
plan_critique_max_rounds: 4       # 默认 4, 可调 2-6
plan_critique_min_rounds: 0       # v9.9.0 (U2): 0=auto (Refactor/System=2, 其余=1); delivery-gate 在 ship 验 design.md 轮数
plan_critique_disabled: false     # 关闭多轮 critique (用户自负责)
skip_impl_subagent_check: true    # 仅当前已完成 CC 9.9.1 sprint 的审计豁免: generator 确实在 isolation:worktree 执行, 但 v9.9.2 tracker 未把 lifecycle 写回主 sprint 账本；pass1-3 + 144/0·72/0/0·11/11 独立佐证, 不伪造记录。新 sprint 开始时必须恢复 false。
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
- `2026-07-10 14:22`: Athena 9.9.1 review pass2=PASS。统一验证 65/65，runtime 30/30，migration 8/8；进入 polish。
- `2026-07-10 14:31`: Athena 9.9.1 polish=READY。architecture、compound、release report 已更新；进入 ship。
- `2026-07-10 14:36`: Athena 9.9.1 已发布。release commit `c0cc8ed` 合并并推送 main；worktree/branch 已清理，roadmap 4/4 complete。
- `2026-07-10 15:15`: CC Athena 9.9.1 设计 Round 1 已落盘。以 CC 9.9.0 为只读基线，对齐 CX 9.9.1；等待 Fable5 review，禁止实现。
- `2026-07-10 21:40`: CC 9.9.1 Fable5 review pass1=REWORK (4 P0: finalVerdict 模板/命令替换绕过/rm glob/PreCompact matcher; 均未被 143/0 套件捕获)。
- `2026-07-10 22:30`: rework_impl 完成 (generator, worktree)。全部 P0/P1 修复+失败驱动用例; 复验 144/0 · 66/0/1 · 11/11 · clean (主 agent 亲跑+探针复证)。
- `2026-07-10 22:50`: pass2=PASS (evaluator)。design Round 3 记录勘误与接受偏离; next_action=polish。ship 前待用户裁决: enabledPlugins 清单 + design §18 开放决策。
- `2026-07-11 00:30`: polish=Pass。guard `#` 注释误报修复 (+4 用例→70/0/1)、exec bit 恢复、validator tempdir 竞态修复、RELEASE.md known-limitations。
- `2026-07-11 01:10`: 用户裁决完成 — 插件清单保留(授权); §18 四决 (model=best/floor 2.1.203/evidence schema 不变/Agent Teams opt-in); ship=merge+push。generator 落 model=best + floor 2.1.203, 144/0·72/0/0(2.1.203+2.1.206 live)·11/11。
- `2026-07-11 01:20`: pass3=PASS (§18 复审), architecture 已同步, roadmap 6/6 completed; stage→ship 待执行 merge+push。
- `2026-07-11 01:35`: CC 9.9.1 已发布。merge (09d7c45) + state (25d4883) 推送 main; 9.9.0 tree 仍 eb1ab06 (AC1); worktree/branch 清理完毕。用户本地 9.9.0 settings 与 codex config 改动未卷入 (保留未提交)。roadmap claude-code-9-9-1-optimization 6/6 complete。

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
- `2026-07-10 13:31:06`: stage=review sprint=2026-07-10-claude-code-9-9-1-impl turn-end
- `2026-07-07 02:24:00`: stage=plan sprint=2026-07-07-f1-orchestrator-framework-design turn-end
- `2026-07-07 01:53:39`: stage=  sprint=  turn-end
