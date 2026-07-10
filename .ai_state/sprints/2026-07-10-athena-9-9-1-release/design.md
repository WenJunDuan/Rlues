---
sprint_slug: "2026-07-10-athena-9-9-1-release"
path: "System"
created: "2026-07-10"
last_updated: "2026-07-10"
---

# Design — 2026-07-10-athena-9-9-1-release

## 背景

Athena 9.9.0 的静态配置可被 CX 0.144.1 加载，但运行语义已漂移：PostToolUse wire 无结构化 exit code、native collaboration 工具不接受旧 shell 语法、fresh setup 漏装 AGENTS 且 provider 为空、模型上下文手工值超目录、agent/state 与 skill schema 不一致。9.9.1 必须修复“能加载但门禁不可信”的核心问题。

## 目标

- 发布 `vibeCoding/codex/9.9.1/.codex` 与 `vibeCoding/claude/9.9.1/.claude`。
- 保持 9.9.0 完全不变。
- 让 CX 0.144.1 的 config、hooks、subagents、skills、setup/migrate 与真实 schema 对齐。
- 用可复跑 fixtures 证明失败不会被记为成功，门禁不能被 SubagentStart 绕过。
- 完成 PACE System 的 runtime-verify、review、polish、architecture、ship。

## 非目标

- 不迁移或覆盖本机现有 `~/.codex`；本次只发布版本包。
- 不更改用户已有 provider endpoint、MCP、项目、桌面或插件配置；不直接编辑、伪造 hook trust store。hook 内容变化后的重新信任由 Codex 与用户完成。
- 不承诺 hooks 覆盖所有 tool path；明确其为 guardrail。
- 不重写 PACE 为第二套状态机。

## 关键决策

1. **版本隔离**：复制 9.9.0 生成 9.9.1；旧目录只用于回归对照。
2. **portable config**：新模板使用 built-in `openai` + Codex 0.144.1 catalog slug `gpt-5.6-sol`，保留 `xhigh`，删除空 custom provider、1M context、900k compact 与 NUX 运行态。
3. **升级保守**：setup 负责 fresh、缺失端补装与同版验证；检测到任一旧版时必须路由 9.9.0→9.9.1 定点迁移，不整文件覆盖用户 config。
4. **证据 fail-safe**：PostToolUse 读取 `tool_response`；仅接受顶层 JSON object 中“整数且非布尔”的 `exit_code`，0=pass、非 0=fail。其他字段、字符串、布尔值、嵌套文本、缺字段与未知对象一律 `unknown`，禁止从自然语言猜测退出状态。
5. **subagent 身份与状态**：v2 `spawn_agent` 只返回 canonical `task_name`，SubagentStart/Stop 才提供真实 `agent_id`。hook 先把 raw event 写 `.ai_state/sprints/{slug}/subagent-events.jsonl`，必填 `schema_version/event/agent_id/agent_type/sprint_slug/timestamp`；主线程每次串行 spawn 后读取唯一新增且未绑定的 Start，再写 `subagent-assignments.jsonl`，必填 `schema_version/agent_id/task_name/role/sprint_slug/timestamp`。若新增 Start 为 0 或 >1，立即停止继续 spawn 并 block。完成握手后 agents 可并行运行。门禁按 `agent_id + sprint_slug` 关联 assignment 与 raw event，最新有效事件必须 Stop；损坏行、孤立/歧义事件或字段类型错误都 block。
6. **native orchestration**：使用当前 surfaced collaboration tools；禁止把 `spawn_agent` 当 shell 命令，禁止 `--cwd`、`assign_task`、裸 `wait`。
7. **worktree 诚实边界**：主线程先创建 worktree；任务携带绝对路径并要求 agent 验证 pwd/workdir。若 surface 支持 managed worktree/独立 task，优先使用；不宣称 Bash hook 能拦 native spawn。
8. **主线程落盘**：read-only critic/reviewer/evaluator 只返回结果；主线程串行写 design/reviews/_index，消除权限冲突与并行覆盖。
9. **单一 sprint schema**：全部当前路径使用 `.ai_state/sprints/{current_sprint_slug}`；`details/` 仅能出现在 migrate 历史转换代码。
10. **skill schema**：SKILL.md frontmatter 只保留官方允许字段；自定义 stage/effort 信息移入正文或 metadata。
11. **GPT-5.6 提示词**：保留 outcome/evidence/permission/stopping invariants；移除通用“极简/可见 CoT/主线程只编排”等互相冲突的绝对表述。
12. **双端边界**：CX runtime-specific 修复不机械复制到 CC；共享 skills/版本/路径/提示词保持语义对称。
13. **gate fail-closed**：从 cwd 向上找到 `.ai_state/` 即视为 Athena 项目；进入 ship 时，`_index.md`、checklist、evidence、review、assignment/event 任一缺失、畸形或解析失败都 block。完全找不到 `.ai_state/` 才静默跳过。
14. **迁移事务性**：单一 orchestrator 覆盖所选 CC/CX endpoints；先完成零写入 preflight 与同一 transaction backup，再定点合并配置、同步 release-owned assets、post-verify，成功后才清理精确记录的 deprecated Athena skill。配置文件原子替换；多文件事务失败时全端回滚。支持 dry-run、幂等重跑与故障注入；敏感值不输出。
15. **setup 状态机**：CC/CX 分别探测，覆盖 fresh、CC-only、CX-only、same-version、old-version 五态；包定位包含仓库根 `vibeCoding/{claude,codex}/9.9.1`。
16. **CX Skill 目录**：分发源码仍位于包内 `.codex/skills`；fresh install 与迁移目标使用 0.144.1 标准用户目录 `~/.agents/skills`，并清理 Athena 自身在 deprecated `~/.codex/skills` 的旧副本，不碰第三方 skill。

## CC/CX 文件级边界

| 类型 | 文件/语义 | 校验方式 |
|---|---|---|
| CX-only | `config.toml`、Python hook wire、native collaboration、Codex agent TOML | strict config、hook schema/fixtures、CX 文本扫描 |
| CC-only | `settings.json`、CJS hook contract、Claude agent Markdown | JSON/Node 校验、CC 自有行为 fixture |
| Shared | PACE stage、sprint 路径、review 主线程落盘、skill 目标、版本与 CHANGELOG | shared semantic parity validator；不要求逐字节相同 |

## 验收标准

- [ ] AC1: `git diff 5eb6189 -- vibeCoding/codex/9.9.0 vibeCoding/claude/9.9.0` 为空。
- [ ] AC2: 9.9.1 CC/CX 目录完整，版本号、AGENTS/CLAUDE、CHANGELOG 与模板为 9.9.1。
- [ ] AC3: CX config 严格解析；默认 provider 可运行配置不含空 base_url；不覆盖模型 context/compact catalog。
- [ ] AC4: PostToolUse 仅在约定的结构化状态可判 pass/fail；字符串、缺字段及不可确认响应均为 unknown；自然语言不得推断状态。
- [ ] AC5: spawn 后通过唯一未绑定 Start 把 canonical `task_name/role` 与真实 `agent_id` 握手；assignment 与 raw SubagentStop 按 `agent_id + current sprint` 关联；Start、其他角色、其他 sprint、孤立/歧义 Stop 均不能满足 generator 门禁；不依赖 Stop exit_code。
- [ ] AC6: `spawn_agent --cwd`、`assign_task`、裸 `wait`、agent TOML shell 调用从 CX 热路径清零。
- [ ] AC7: 非 migrate 代码中的 `.ai_state/details` 引用清零。
- [ ] AC8: read-only agents 无直接写文件指令；reviewer/spec-compliance 返回结果后由主线程合并。
- [ ] AC9: 31/31 CX skills 与对应 CC skills 通过官方 quick_validate。
- [ ] AC10: setup 的 fresh/CC-only/CX-only/same-version/old-version fixtures 全部通过；复制 AGENTS.md；CX skills 安装到 `~/.agents/skills`；动态计数；不修改 trust store，并明确重新信任提示。
- [ ] AC11: 可执行 migrate orchestrator 完成 CC settings/Athena hooks、CX config/hooks、双端资产与 CX skill 目录升级；dry-run、单 transaction backup、原子配置写、幂等、四阶段故障注入全回滚通过；provider/MCP/projects/desktop/plugins/第三方资产与未知用户字段保持不变且日志不泄露。
- [ ] AC12: hooks 文档准确说明 Bash/apply_patch/MCP 支持与 unified_exec 不完整边界；SessionStart 覆盖 clear。
- [ ] AC13: package validation 覆盖 TOML/JSON/Python/Node/YAML/frontmatter/behavior/diff-check，并运行真实 Codex 0.144.1 strict config 与 hook startup/schema 加载；`SessionStart` matcher 含 `clear`。
- [ ] AC14: runtime-verify.md 包含正常、边界、异常场景与命令输出。
- [ ] AC15: reviews/pass1.md 含 reviewer、Spec Compliance、Evidence Cross-Check、最终 VERDICT。
- [ ] AC16: cleanup-pass.md、architecture 更新、compound learning 完成。
- [ ] AC17: 最终 main 包含发布提交；临时 worktree/branch 清理；本地 main 与 origin 状态明确报告。
- [ ] AC18: ship gate 对缺 assignment、缺 generator Stop、agent_id 不匹配、握手歧义、checklist 未完成、evidence 为空/仅 unknown/含 fail、review 无最终 PASS、日志畸形逐项 block；至少一条可信 pass 且无 fail 的完整证据链才可 pass。
- [ ] AC19: 每个行为修复先保存失败 fixture 证据，再由同一 fixture 转绿。
- [ ] AC20: 固定 base commit `5eb6189` 验证 9.9.0 路径零改动；9.9.1 发布身份完整，非历史语境无未来版本串。
- [ ] AC21: CC/CX 文件级非对称矩阵完成；shared semantic parity 与 runtime-specific 独立验证均通过。

## 实现要点

- 先复制版本目录，再先写 release validator 与 synthetic fixtures，保存空 provider、手工 context/compact、strict config/schema、false-pass、Start 绕过与 gate 缺件的预期失败结果；随后按 CX runtime / shared contracts / installer-doc 三个不重叠写集分派。
- fixtures 直接喂 0.144.1 wire JSON；PostToolUse 字符串响应必须得到 unknown。
- delivery-gate 解析结构化 assignment/event log、checklist、evidence 与 review verdict，不以任意字符串命中作为完成。
- 配置迁移使用临时文件、前后解析、受保护片段比对与原子替换；不打印 user config 内容。
- validation 脚本只输出路径、计数、pass/fail，不输出 provider/MCP 密钥或 endpoint。

## File Structure Plan

```text
vibeCoding/
├── codex/9.9.1/
│   ├── CHANGELOG.md
│   └── .codex/
│       ├── AGENTS.md
│       ├── config.toml
│       ├── hooks.json
│       ├── hooks/*.py
│       ├── agents/*.toml
│       ├── standards/*.md
│       └── skills/*
├── claude/9.9.1/
│   ├── CHANGELOG.md
│   └── .claude/{CLAUDE.md,settings.json,hooks,agents,rules,skills}
└── scripts/validate-athena-9.9.1.py
.ai_state/
├── roadmap/athena-9-9-1-release/*
├── sprints/2026-07-10-athena-9-9-1-release/*
├── architecture/*
└── compound/*
```

release sprint 仅保存跨 item 总设计，不维护可执行 checklist；所有任务状态只存在各 roadmap item 的 `checklist.yaml`。

## 风险与权衡

- Hook wire 不提供退出码：选择 unknown 而非猜测，牺牲自动 pass 率换取证据可信度。
- 不覆盖 existing config：升级逻辑更复杂，但避免破坏 provider/MCP/desktop 状态。
- native spawn 无 cwd：降级为可验证路径纪律并记录真实边界，不伪造机械保证。
- GPT-5.6 prompt 瘦身：只删除冗余/冲突，不削弱 PACE 的验收、证据和权限约束。
- hook 内容哈希变化：不触碰 trust store；把“待重新信任”作为显式升级结果，而非宣称状态不变。

## 历史决策对齐

- 与 `compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md` 一致：拿不到可靠 usage/status 时记录 unknown，不估算。
- 与 `compound/2026-07-08-learning-hook-order-and-worktree-counts.md` 一致：多 hook 无顺序保证；计数与状态必须现场验证。

---

## Round 1 (initial draft by main agent, xhigh)

设计覆盖审计中的全部 P0/P1，并将 P2 prompt/packaging debt 纳入同一发布。实现以 fail-safe 证据、portable install、native orchestration、主线程落盘四条主线收敛。

### Critic Findings

- REVISE：generator 身份缺机械关联；gate 异常可能放行；fixtures 顺序违反 TDD。
- REVISE：roadmap item 复用 sprint；setup/migrate 状态机、hook trust、负向 gate 矩阵与双端边界不完整。

## Round 2 (revision by main agent, xhigh)

已加入结构化 assignment/event 关联、Athena ship fail-closed、测试先行、独立 sprint、事务迁移、五态 setup、真实 hook schema 加载、七类 gate 负向矩阵、固定基线与 CC/CX 文件级边界。

### Critic Findings

- REVISE：可靠状态字段、JSONL schema 与 Athena 项目判定边界仍需写死。
- REVISE：setup 首装表述冲突；release checklist 与 item checklist 构成双状态机；config 红灯 fixture 不完整。

## Round 3 (revision by main agent, xhigh)

已限定唯一可靠状态为顶层非布尔整数 `exit_code`；定义 assignment/event schema v1 与损坏行处理；setup 分流 fresh/补装/同版/旧版；移除 release 可执行 checklist；补齐 config 红灯与固定 Git 基线命令。

### Critic Verdict

PASS：上一轮阻塞项全部闭合，可进入 impl。

### Official Source Adjustment

Codex 0.144.1 源码确认用户 skills 标准目录为 `~/.agents/skills`，`$CODEX_HOME/skills` 为 deprecated compatibility；模型目录确认 `gpt-5.6-sol`。本调整发生在功能修复写入前，validator 与实现统一采用原生值。

### Post-Impl Source Correction

首轮 runtime review 发现 v2 spawn 输出不含 `agent_id`，且 gate 接受 unknown/fail evidence。设计改为 raw lifecycle event + spawn 后唯一 Start 握手；evidence gate 要求至少一条可信 pass 且不得含 fail。`design_changed_after_impl=true`，修复后必须重新 review。

### Installer Review Correction

installer review 发现 config transformer 不能代表完整升级链。9.9.1 增加双端 transaction orchestrator；setup/migrate 行为 fixtures 与 release validator 必须执行真实流程和故障回滚，不再只检查文案。
