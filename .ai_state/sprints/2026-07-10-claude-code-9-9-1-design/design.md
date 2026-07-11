---
sprint_slug: "2026-07-10-claude-code-9-9-1-design"
roadmap_slug: "claude-code-9-9-1-optimization"
path: "System"
target_version: "Athena CC 9.9.1"
baseline_version: "Athena CC 9.9.0"
status: "approved_for_impl_post_review_required"
created: "2026-07-10"
---

# Design — Claude Code Athena 9.9.1

## 1. Outcome

构建一个基于 CC 9.9.0 的可信 patch：修复当前 Claude Code 合约漂移，令 CC 与 CX 9.9.1 能通过同一 `.ai_state` 继续、review 和 ship；同时用 CC 原生模型路由、subagent、worktree、hooks 与安全能力提升质量，但不建立第二状态机。

## 2. Baseline and authority

- 唯一代码基线：`git HEAD:vibeCoding/claude/9.9.0/.claude`，tree object `eb1ab06bae8e9a9bd576643e941c4e5d59360fb1`。
- 共享语义基线：已发布 `vibeCoding/codex/9.9.1/.codex`，tree object `1ee93329e44576750cca132d1f015243ac7a69f2`。
- 现有 CC 9.9.1 目录是候选实现，不是设计真相。实现阶段从 9.9.0 创建干净 staging tree，再逐项应用已批准设计；候选目录仅用于差异复用审计。
- 真实用户 `~/.claude`、当前未提交的 9.9.0 settings、MCP、plugins、credentials 与 hook trust 均不属于覆盖范围。

## 3. Official target

| 层级 | 版本 | 行为 |
|---|---:|---|
| 兼容下限 (§18.2 用户裁决 2026-07-10) | Claude Code 2.1.203 | 原生 worktree 强边界 + `--effort ultracode`; 硬最低版本从 2.1.197 上移, 消除 2.1.197-2.1.202 的 worktree 降级路径 |
| 发布验证目标 | 2.1.206 latest | 全设计能力矩阵 |

版本来自 npm `@anthropic-ai/claude-code`；功能依据官方 [Hooks](https://code.claude.com/docs/en/hooks)、[Subagents](https://code.claude.com/docs/en/sub-agents)、[Worktrees](https://code.claude.com/docs/en/worktrees)、[Settings](https://code.claude.com/docs/en/settings)、[Model config](https://code.claude.com/docs/en/model-config)、[Agent teams](https://code.claude.com/docs/en/agent-teams)。

## 4. Current blocking findings

### P0-1 · WorktreeCreate replaces native git worktree

9.9.0 注册 `WorktreeCreate`，当前脚本仅创建目录并返回路径。官方契约规定：一旦注册该 hook，就完全替换 Claude Code 原生 git worktree 创建。默认包必须删除 Git 场景的 WorktreeCreate/Remove hook，改用原生 `isolation: worktree`；非 Git VCS 才允许专用自定义 hook。

### P0-2 · Evidence wire is false

现 collector 读取 `tool_output.exit_code`，而 CC PostToolUse 使用 `tool_response` 且只在成功后触发；代码还把缺失 exit code 默认成 0。9.9.1 必须以 PostToolUse 记录成功、PostToolUseFailure 记录失败，未知不推断，写文件成功不得冒充测试通过。

### P0-3 · Persisted max effort is invalid

`settings.effortLevel` 官方持久值只有 `low|medium|high|xhigh`。`max` 只用于会话参数、环境变量或 agent frontmatter。默认持久设置改为 `xhigh`；`max` 仅按角色/任务显式使用。

### P0-4 · Global subagent model overrides every role

`CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5` 优先级高于 invocation 与 agent frontmatter，导致 critic/evaluator 的 `model: opus` 实际无效。默认包删除该全局覆盖，恢复角色模型路由。

## 5. Design invariants

1. 9.9.0 目录零改动。
2. `.ai_state` 是 CC/CX 唯一跨端状态真相；平台 session/team/task 数据不是替代品。
3. 主 agent 对结果和状态写入负责；critic/reviewer/spec/evaluator 只返回。
4. 无可靠字段时记录 unknown，不从文本猜 exit、身份或完成状态。
5. Feature+ ship fail-closed；非 Athena 项目不干预。
6. CC/CX 对齐语义、文件和门禁强度；不伪造工具、模型、hook payload 对称。
7. Agent Teams 默认关闭，不能成为发布依赖。
8. Setup/migrate 定点合并，不覆盖用户整份配置，不修改 trust store。

## 6. Shared state contract

### 保留

- `_index.md`
- `sprints/{slug}/{route-note,design,checklist,evidence,runtime-verify,reviews,cleanup-pass}`
- `roadmap/{slug}/items.yaml`
- `requirements/`、`architecture/`、`compound/`
- PACE 9 stages、path、review 2+1、polish/architecture 门禁

### 禁止恢复

- `.ai_state/details/`
- agent 直接并行写 `design.md`、`passN.md`、`_index.md`
- 固定只读 `pass1.md` 的 review 选择逻辑
- private CoT 落盘

### 新机器账本

CC 与 CX 共享完全相同 schema：

- `subagent-events.jsonl`: `schema_version,event,agent_id,agent_type,sprint_slug,timestamp`
- `subagent-assignments.jsonl`: `schema_version,agent_id,task_name,role,sprint_slug,timestamp`

CC SubagentStart 原生提供 `agent_id + agent_type`，但 `task_name` 仍由主 agent 的任务意图产生。为避免伪造，CC 也采用“唯一新增 Start → 主 agent assignment”握手；不把 agent_type 冒充 task_name。Start 时冻结 sprint 映射，Stop 按 agent_id 回写原 sprint，不读取可能已经切换的当前 sprint。

`subagent-log.md` 继续作为人类视图，但不作为机器门禁唯一依据。

## 7. Hook architecture

| Event | 默认用途 | Blocking |
|---|---|---|
| SessionStart startup/resume/clear | 项目探测、版本提示、恢复状态 | 否 |
| InstructionsLoaded | 审计 CLAUDE/rules 实际加载 | 否，async |
| ConfigChange | 记录 settings/skills 漂移；默认不拦用户配置 | 可选策略 |
| PreToolUse | 仅精确危险命令和 stage push 门禁 | 是 |
| PostToolUse | 记录明确成功；区分 write/test/build | 否 |
| PostToolUseFailure | 记录明确失败、error、duration | 否 |
| PostToolBatch | 可选并发批次归并；不得复制完整大响应 | 否 |
| SubagentStart | raw Start + 冻结 sprint | 否 |
| SubagentStop | raw Stop + 人类日志；不猜 exit | 可反馈继续 |
| Stop | delivery gate + checkpoint/continuation | 是 |
| StopFailure | API/模型失败审计 | 否 |
| PreCompact/PostCompact | 快照与恢复; PreCompact matcher 官方取值 `manual\|auto` | 否 |
| Notification | agent_needs_input/agent_completed 过滤在脚本内部做; matcher 留空全匹配 (官方 matcher 不承诺该类型值) | 否 |
| TaskCreated/TaskCompleted/TeammateIdle | 仅 Agent Teams opt-in profile | 是/可反馈 |

门禁与 raw ledger 必须同步、确定性；telemetry 才能 async。`if` 只做性能过滤，不是安全边界。PreToolUse 不再扫描任意引用文本命中关键字；注册层用官方 Bash permission pattern 缩小调用面，脚本内部只解析实际命令结构。

## 8. Delivery gate parity

CC gate 与 CX 9.9.1 对齐：

- Athena 项目存在但 `_index.md` 缺失/畸形：block。
- Feature/Refactor/System：generator assignment + Start + Stop 完整关联。
- orphan、duplicate、跨 sprint、agent_type 不一致、Stop 早于 Start/assignment：block。
- checklist 所有 task 必须 completed。
- evidence 至少一条可信 validation pass；任何 fail 或 unknown-only：block。
- roadmap slug、total_items、item slug/status 可解析且全部 completed。
- review 选择最新数字 `passN.md`；旧 PASS 不能覆盖新 REWORK。
- Reviewer + Spec 并行返回，主 agent 合并；Evaluator 后跑。
- ship 只接受最终 PASS；CONCERNS 不自动 ship。
- design 修改后重新 review。
- Refactor/System 强制 runtime-verify、cleanup-pass、architecture；Bugfix 强制 fix-note。
- block reason 必须给明确解锁动作。

CC 可比 CX 更严格地要求 validation kind，但不能写出 CX 无法解析的共享 schema。若要增强共享 evidence schema，必须作为 CC/CX 同步 contract change 单独确认。

## 9. Model and agent policy

### Main session

- 默认 (§18.1 用户裁决 2026-07-10)：`model: best` — org 有 Fable5 权限则用 Fable5, 否则回退最新 Opus (官方别名, 见 [Model config](https://code.claude.com/docs/en/model-config))。质量优先, 全程用最强模型 (无 opusplan 的 plan/exec 分离); 成本换质量为用户明确取舍。
- `effortLevel: xhigh`；不持久化 max/ultracode。
- `fallbackModel: ["opus", "sonnet"]`。
- System/Refactor design 可按 `_index.plan_model=fable` 显式使用 Fable5；不把 Fable 强制给所有 Quick/Feature。
- 默认不硬编码 `ANTHROPIC_DEFAULT_*`；第三方 provider/gateway 由用户或专用 profile pin。

### Role defaults

| Role | Model | Effort | Permission | Background | Isolation |
|---|---|---:|---|---|---|
| critic | fable, fallback opus | xhigh | plan/read-only | false | none |
| architect | fable, fallback opus | xhigh | plan/read-only | false | none |
| reviewer | sonnet | high | plan/read-only | true | none |
| spec-compliance | sonnet | high | plan/read-only | true | none |
| evaluator | opus | xhigh | plan/read-only | false | none |
| generator | sonnet; System 可 override opus | high/xhigh | write | false | path-dependent |
| polish-worker | sonnet | high | write | false | worktree for red zone |

read-only agents 使用 `permissionMode: plan`、`disallowedTools: Write,Edit,Agent`、合理 `maxTurns`。使用官方 `skills` frontmatter 预载角色 skill；不启用 subagent persistent memory，避免与 `.ai_state` 形成第二状态源。

## 10. Worktree design

- 删除默认 Git WorktreeCreate/Remove hook，恢复 Claude Code 原生 git worktree。
- `worktree.baseRef: "head"`，保证未推送 commit/feature HEAD 被带入隔离区。
- floor 已上移到 2.1.203 (§18.2), 所有支持版本均宣称强 worktree 边界; 不再需要 2.1.197-2.1.202 的人工创建降级路径。
- 黄区 generator 不强制 isolation；红区 generator/polish 使用 `isolation: worktree`。
- dirty tree 不能假装被带入新 worktree：先 commit/stash/明确允许写集，再启动。
- 用 SubagentStart/Stop、`git worktree list` 与主 agent现场检查记录生命周期，不用替换创建流程的 hook 做旁路 tracking。

## 11. Prompt, skills and review

- 保留 outcome-first、验收、权限、证据、停止条件。
- Route Note 只写候选、证据、权衡、决定、置信度；不要求暴露私有 CoT。
- 所有 `Task tool` 陈旧文本改为官方 `Agent`/subagent 表述。
- CC skill frontmatter保留 CC 官方字段，包括合理的 `effort`；只删除非官方 `attach_to_stages`。
- CC `.claude/rules` 保留，不复制 CX `standards` 平台实现。
- `/goal` 和 CC workflows 继续承担长循环；不伪装成 CX Goals API。
- Review 统一为 latest passN + 2+1 + 主 agent 单写。

## 12. Settings and security

- 新包默认配置必须通过官方 settings schema；删除 `_comment*` 私有键，说明移到 CHANGELOG。
- 移除全局 `CLAUDE_CODE_SUBAGENT_MODEL` 与不必要的模型 pin。
- 不默认启用 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`。
- 权限从宽泛 `Read(**)/Write(**)` 收敛：测试、构建、只读 Git 可自动；安装、外网、SSH、publish、force push 保持 ask/deny。
- 增加敏感读取 deny 建议：`.env*`、credentials、keys、secrets；实际用户级 paths 由 setup/doctor 展示并确认。
- sandbox 作为可验证 profile，不在 patch 中无条件强开破坏现有 Docker/SSH/VM 流程。
- Hook 校验 cwd/path、拒绝 traversal；不拼接 payload 字段到 shell。
- `git push` 仍要求 stage=ship；逃生开关必须显式、可审计，不能由 subagent自行添加。
- 第三方 plugins/marketplaces 保留用户选择，不因缺失阻断 Athena 核心启动。

## 13. Agent Teams boundary

- 默认关闭、experimental、非发布依赖。
- 仅可用于 System/Refactor 的并行研究、独立 review、竞争假设或互斥模块。
- 启用必须由用户明确批准，建议 3–5 teammates；同文件写入禁止。
- Team task list 仅运行时协调；`.ai_state/checklist.yaml` 才是项目真相。
- 可用 TaskCompleted/TeammateIdle hook 要求 evidence，但不能替代 delivery gate。
- 不承诺 resume、nested team、即时 task status 或权限代理。
- 若 Fable5 判断 patch 风险过大，Agent Teams 整体延后，不影响 9.9.1 core release。

## 14. Setup and migrate

9.9.0→9.9.1 使用三方定点合并：old baseline、user current、target defaults。

- 仅当 `effortLevel` 仍为 9.9.0 默认 max 时改为 xhigh。
- 仅删除精确 Athena 默认的 `CLAUDE_CODE_SUBAGENT_MODEL` 与 model pins。
- 替换 Athena-owned hooks；private/mixed hooks 与未知字段保留。
- 旧宽权限只按精确 9.9.0 默认项删除；用户新增权限原样保留并报告。
- 保留 MCP、plugins、marketplaces、credentials、provider、trust。
- 配置先 stage/parse，再原子替换；所选端共享 transaction backup；任一阶段失败全回滚。
- 支持 dry-run、CC-only、幂等、故障注入；日志不输出 secret/value。
- 现有用户对 9.9.0 settings 的未提交自定义必须进入 migration fixture，证明不会被覆盖。

## 15. Validation matrix

### Static

- JSON schema、Node syntax、agent/skill frontmatter、链接、junk、版本身份。
- 固定 Git object 验证 9.9.0 零改动。
- CC/CX shared contract parity；平台专属文件不要求字节相同。

### Hook behavior

- 官方 SubagentStart/Stop、PostToolUse、PostToolUseFailure、Stop/StopFailure fixtures。
- 成功、失败、interrupt、缺字段、畸形输入、并发 batch。
- Start/Stop 并发追加无半行、丢行、跨 sprint。
- quoted text 中出现 `git push`/危险词但实际是只读命令时不得误拦；真实 push/destructive command 必须阻断。

### Gate

- 完整正例至少 1 条。
- 负例不少于 25 条：assignment/event/checklist/evidence/review/roadmap/runtime/polish/architecture 全部覆盖。
- CC 生成的共享 ledgers 可被 CX 9.9.1 fixture 解析；CX artifacts 可被 CC gate 解析。

### Runtime

- Claude Code 2.1.197 与 2.1.206 两档临时 HOME。
- 2.1.203+ 原生 worktree E2E：baseRef=head、主 checkout 零写入、清理行为。
- 实际检查每个 agent 的 model/effort/permission/background，不只读配置文本。
- reviewer/spec 并行，passN 落盘后才启动 evaluator。
- migrate fresh/customized/dry-run/idempotent/rollback/private hooks/plugins。

## 16. Acceptance criteria

- [ ] AC1: committed CC 9.9.0 tree object 保持 `eb1ab06...`。
- [ ] AC2: 实现从 9.9.0 clean staging tree 产生，现有 9.9.1 候选不作为基线。
- [ ] AC3: settings 在 2.1.197 与 2.1.206 均可加载；版本降级明确。
- [ ] AC4: `effortLevel=xhigh`；无持久 max/ultracode。
- [ ] AC5: 无全局 subagent model 覆盖；角色实际模型与设计一致。
- [ ] AC6: 默认 Git 模式无 WorktreeCreate/Remove override；2.1.203+ 原生 isolation 通过。
- [ ] AC7: PostToolUse/PostToolUseFailure 分别产生 pass/fail；缺失不默认成功。
- [ ] AC8: CC/CX 使用同一 assignment/event schema；task_name 不由 agent_type 伪造。
- [ ] AC9: Stop 回写 Start 冻结的 sprint；并发与切换 sprint 不错投。
- [ ] AC10: gate 对缺失、畸形、orphan、unknown-only、fail 全部 block。
- [ ] AC11: checklist 与 roadmap 全 completed；latest passN 最终 PASS 才可 ship。
- [ ] AC12: Review 2+1；只由主 agent 写 design/passN/index。
- [ ] AC13: read-only agents 有工具、permission、turn 限制。
- [ ] AC14: PACE/.ai_state 保持兼容；无非 migrate `details/`。
- [ ] AC15: PreToolUse 无引用文本误报；真实危险命令仍阻断。
- [ ] AC16: Agent Teams 默认关闭，启用不产生第二状态机。
- [ ] AC17: setup/migrate 保留用户配置、private hooks、plugins、trust 与 secrets。
- [ ] AC18: 9.9.0→9.9.1 transaction 支持 dry-run、幂等、故障全回滚。
- [ ] AC19: stable 2.1.197 + target 2.1.206 双版本矩阵通过。
- [ ] AC20: release validator、runtime-verify、review、polish、architecture、compound 全绿。
- [ ] AC21: Fable5 post-implementation review 完成，findings 合并后才允许发布。
- [x] AC22: 用户已明确批准先实现、后由 Fable5 review 修改。

## 17. File structure plan

```text
vibeCoding/claude/9.9.1/.claude/
├── CLAUDE.md
├── settings.json
├── agents/{architect,critic,evaluator,generator,polish-worker,reviewer,spec-compliance}.md
├── hooks/
│   ├── session-start.cjs
│   ├── pre-bash-guard.cjs
│   ├── evidence-collector.cjs
│   ├── subagent-tracker.cjs
│   ├── delivery-gate.cjs
│   ├── config-change-audit.cjs
│   └── stop-failure-recorder.cjs
├── skills/{pace,athena-review,athena-setup,athena-migrate,...}
└── rules/

vibeCoding/scripts/
├── validate-athena-9.9.1.py
├── test-athena-claude-9.9.1-runtime.cjs
└── fixtures/athena-9.9.1/claude/*
```

删除默认 Git `WorktreeCreate/Remove` hook 注册；非 Git VCS 示例不得进入默认 settings。

## 18. Open decisions — RESOLVED (用户裁决 2026-07-10, ship 前)

| # | 决策 | 结论 | 落地 |
|---|---|---|---|
| 1 | 主模型 opusplan vs best | **best** | settings.json model=best (§9 已改) |
| 2 | floor 2.1.197 vs 2.1.203 | **2.1.203** | §3 表已改; runtime 矩阵下限 2.1.203, §10 删 2.1.197-2.1.202 降级路径 |
| 3 | CC assignment 复用 CX 握手 vs Start 自动生成 | **复用 CX 唯一握手** | 已实现 (§6, subagent-tracker assign) |
| 4 | evidence 加 validation-kind 强约束 vs 保持 | **保持 CX 9.9.1 schema 不变** | 两端 gate 仅锚 tool_use_id/result; kind 作为未来 CC/CX 同步 contract change |
| 5 | 删默认 WorktreeCreate/Remove hook | **删除** | 已实现 (worktree-tracker.cjs 删除, AC6) |
| 6 | 权限收敛是否超兼容范围 | **未超** | reviewer 判定: test/build/只读 git 自动, install/网络/push ask-deny; 兼容 |
| 7 | Agent Teams opt-in vs 延期 | **opt-in 保留** | 默认关, 边界见 §13 |
| 8 | PASS-only ship vs 保留 CONCERNS 自动 ship | **PASS-only** | 已实现 (§8, delivery-gate finalVerdict!=PASS 即 block) |
| 9 | 6-item roadmap 保持 vs 拆两版本 | **保持单版本** | 兼容修复 + 原生增强同属 9.9.1, 已全绿; 不拆 |

### 需 generator 落地的代码改动 (§18.1 + §18.2)

- settings.json: `"model": "opusplan"` → `"best"`
- 兼容矩阵 floor: 2.1.197 → 2.1.203 (runtime-verify.md 测试档、validator/runtime 版本断言、§10 worktree 降级段删除)

## Round 1 — Codex xhigh + read-only architect

设计已吸收官方 Claude Code 2.1.206 contract、CC 9.9.0 baseline audit、CX 9.9.1 shared contract 与独立 architect findings。初始建议为 Fable5 pre-review。

### Critic Findings

PENDING — 由用户调用 Fable5，按 `fable5-review-brief.md` 独立审查。主线程收到结果后追加 Round 2 并修订设计。

## Round 2 — User implementation authorization

2026-07-10 用户明确选择“先实现，再叫 Fable5 review 修改”。该决定解除 pre-review 实现锁，但不解除发布锁：实现、验证完成后仍须 Fable5 给出 verdict，所有 P0/P1 必须修复并重新验证，最终 PASS 后才可 ship。

## Round 3 — Fable5 post-implementation review (pass1)

2026-07-10 Fable5 会话内 2+1 交叉审查完成, VERDICT=REWORK (4 P0 + 5 P1 + 2 P2), 完整 findings 见 `../2026-07-10-claude-code-9-9-1-impl/reviews/pass1.md`。

### Critic Findings

- 设计勘误 (本 Round 已修): §7 原把 `agent_needs_input|agent_completed` 写成 PreCompact 语义行, 实现照抄进 settings.json PreCompact matcher → compact-snapshot 永不触发。已改为 PreCompact matcher `manual|auto`, Notification 过滤下沉脚本内部。
- ~~设计勘误 (待修): §2 tree hash 口径~~ pass2 复核证伪: `git rev-parse daf591f:vibeCoding/claude/9.9.1/../9.9.0/.claude` = HEAD = `eb1ab06...`, 与 §2 记录完全一致, pass1 该条为误报, AC1 PASS 无保留。
- AC2 方法论偏离记录为接受: 实现为候选 9.9.1 目录原地增量编辑 (非字面"清空重建"), 等价性由 pass1/pass2 全量 diff 审计 + 9.9.0/codex 零触碰复核背书; §2 表述不再追改。
- CX 同构缺陷 (超出本 patch 范围, 移交下一 CX patch): `delivery-gate.py:328` finalVerdict 同样解析不了粗体判定行; `delivery-gate.py:370-378` gitLines 同样静默吞错。
- rework 授权: 按 evaluator 优先级在 worktree `Rlues-cc-9.9.1-impl` 内修复, 每个 P0/P1 配新增失败用例, 重跑全绿后进 pass2。settings.json 默认插件清单 (P1-5) 与 §18 开放决策留待用户裁决, 本轮不动。
