---
sprint_slug: "2026-07-25-athena-9-9-6-prompt-engineering"
path: "System"
created: "2026-07-25"
last_updated: "2026-07-25"
document_status: "critic-pass-ready-for-bottom-draft"
implementation_authorized: true
git_commit_authorized: false
roadmap_slug: "athena-9-9-6-prompt-engineering"
baseline_release: "9.9.3"
target_release: "9.9.6"
---

# Design — Athena 9.9.6 Prompt Architecture v3.1

## 1. Outcome

以已发布、不可变的 Athena 9.9.3 为唯一模板，构建两个自包含的 9.9.6 endpoint：

- Claude Code 2.1.219+ / Opus 5；
- Codex 0.145.0+ / GPT-5.6；
- 同时覆盖 CLI、Codex App、ChatGPT login、OpenAI API Key 与用户自定义 gateway；
- 保留 PACE 4 core + 5 conditional stage 与 `.ai_state` 单一真相源；
- 不引入 shared contracts、renderer、第二状态树或新的 runtime capability schema。

本 sprint 只产出可 review 的底稿和本地验证证据，不 commit、push 或 release。

## 2. Locked decisions

1. `vibeCoding/claude/9.9.3` 与 `vibeCoding/codex/9.9.3` 不修改；9.9.6 从它们 fork。
2. CC/CX 仅对齐语义，不伪造工具、hook、agent 或配置对称。
3. 所有长期合同归属各 endpoint 的既有 prompt/skill/reference/release 架构。
4. 不创建 `shared-skills/`、`contracts/`、renderer、`.trellis`、OpenSpec 状态树或 `runtime-capabilities.yaml`。
5. Codex 使用内置 `model_provider = "openai"`；不定义空 `[model_providers.openai]`。
6. 保留 WSL acknowledgement、`[desktop]`、plugins、CLI/App 用户态支持。
7. 测试代码、fixtures、完整输出与 A/B 数据只保存在本地，不进入 Git。
8. 用户指定目录树优先于旧计划中的 `scripts/tests/` 假设。
9. 9.9.6 不压缩 PACE stage 数量，不批量删除 26 skills。
10. `.ai_state` 优化拆成注入预算和保留策略；不以磁盘总大小直接决定删除状态。

## 3. Target tree

```text
vibeCoding/
├── claude/9.9.6/
│   ├── .claude/{CLAUDE.md,settings.json,agents/,skills/,hooks/,rules/}
│   ├── AI-MIGRATION-GUIDE.md
│   └── RELEASE.md
├── codex/9.9.6/
│   ├── .codex/{AGENTS.md,config.toml,agents/,skills/,hooks/,standards/}
│   ├── AI-MIGRATION-GUIDE.md
│   ├── CHANGELOG.md
│   └── RELEASE.md
└── scripts/                       # local-only; no Git commit
    ├── validate-athena-9.9.6.*
    ├── test-*-9.9.6-runtime.*
    └── evals/athena-9.9.6/
```

Release adapter 必须可被 Git 发现。仓库根 `.gitignore` 的 `.claude/` 改成 `/.claude/`，只忽略根用户态目录，不吞 `vibeCoding/claude/*/.claude/`。

## 4. Architecture

```mermaid
flowchart LR
    U["User request"] --> C["Endpoint root prompt"]
    C --> P["PACE route + stage references"]
    P --> A["Platform-native agents / tools / hooks"]
    A --> S[".ai_state/_index.md + bounded pointers"]
    S --> G["Spec and delivery gates"]
    G --> E["Local-only tests and evals"]
```

双端各自自包含：

- 根 prompt 保留宪法级不变量；
- `pace/references/` 保存 stage、orchestration、hook 和平台合同；
- role/skill frontmatter 控制发现与调用；
- hooks 只强制平台能真实观察的边界；
- 本地 parity 测试比较关键不变量，不生成 endpoint 文件。

## 5. Claude Code baseline migration

### 5.0 User override · quality-first role matrix

用户最终确认：主会话保持 `model: best`；architect/critic 使用 Fable，evaluator 与 generator/reviewer/spec-compliance/polish-worker 使用 Opus。发行模板不得设置 `CLAUDE_CODE_SUBAGENT_MODEL`，避免全局变量覆盖角色 frontmatter。

### 5.1 底稿立即应用

- 版本标识改为 9.9.6；
- `model = "best"` 与 alias fallback 保留，不 pin dated Opus/Sonnet ID；
- 删除旧 `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5` 与 dated Opus/Sonnet pins；保留 Fable 5 alias pin；
- 保留 root `effortLevel = "xhigh"`，各 agent frontmatter 可按角色覆盖；
- API timeout 更新为官方 600 秒；保留 attribution、installation-check 与 privacy 显式偏好；默认已开的 Tool Search 不重复配置；
- `settings.proxy.json` 提供 6152/6153 本地代理 overlay，默认不加载；
- permissions、worktree、必要 hooks/plugins 保留；
- fresh package 的 `permissions.defaultMode` 使用官方有效值 `default`；不存在 `manual` 枚举。迁移时不得覆盖用户已有的 `default` / `acceptEdits` / `plan` / `auto` / `dontAsk` / `bypassPermissions` 选择。

### 5.2 角色策略

- architect / critic：Fable；evaluator / generator / reviewer / spec-compliance / polish-worker：Opus；
- root effort 为 xhigh；角色 frontmatter 保持 3×xhigh + 4×high；
- 绿区任务禁止无必要委派；
- 不保留 `double-check`、`re-verify`、`use a subagent to verify` 等 legacy coaxing；
- TDD、真实测试、证据和 gate 不是 legacy verification，不删除。

## 6. Codex 0.145.0 baseline migration

### 6.1 Provider and user surfaces

- `model_provider = "openai"`；
- `model = "gpt-5.6-sol"`；
- 保留 `windows_wsl_setup_acknowledged = true`；
- 保留 `[desktop]` 与 plugins；
- 保留当前显式 approval/sandbox 产品选择，迁移时 preserve 用户覆盖；
- API Key 和 ChatGPT login 均走内置 provider；用户已有 `openai_base_url` 或 gateway 只 preserve，不由发行模板伪造空值。

删除：空 custom provider、1M/900k 手工上下文元数据、experimental memories、stable/default-on feature 重复开关、unstable-warning suppression、26 条手工 skill 注册。

### 6.2 Multi-agent V2 exact split

- `[features.multi_agent_v2]`：显式 `enabled = true`；保存 V2 的并发、等待、提示和 tool metadata 配置；
- `[agents]`：通用 enabled、默认 subagent model/reasoning、interrupt 与 roles；
- `[agents].max_depth` 是 V1-only，V2 忽略，因此不能作为 Athena depth 门禁；
- Athena 的嵌套限制继续由 orchestration policy、spawn binding 和 runtime test 强制；
- 不保留兼容 no-op 的 `job_max_runtime_seconds`。

## 7. Skills

26 个现有 skills 全量从 9.9.3 fork。9.9.6 只做四类提炼：

1. frontmatter description 回归“何时用 / 做什么 / 不做什么”；
2. setup、migrate、init、preferences、checkpoint、vm 等高影响 skill 禁止模型隐式触发；
3. CC 使用官方 `disable-model-invocation` 等 invocation 控制，不能把 `user-invocable: false` 当成禁止模型调用；
4. CX 使用 endpoint-local `agents/openai.yaml` 控制 `allow_implicit_invocation`，显式调用仍可用。

Pi 启发的 N9 审计在 release 时统计：根 prompt、26 skill metadata、SessionStart、breadcrumb 的 bytes；tokenizer 不可得时 token 保持 unknown，不伪造换算。

## 8. PACE

PACE 状态机不改名、不合并：

- 4 core：plan / impl / review / ship；
- 5 conditional：brainstorm / roadmap / design / runtime-verify / polish；
- root prompt 只保留路由入口和铁律；
- `pace/references/stages.md` 是 stage 义务真相；
- hook breadcrumb 只注入当前 stage 摘要；
- gate 负责机械可判定项，skill 负责判断性流程。

Spec Kit 启发的 N10 只检查 roadmap → design → checklist 的 slug、依赖、AC/design_ref 和 status 一致性，不增加 schema/renderer/DAG scheduler。

## 9. AI state

`.ai_state` 目录模型保持不变。优化分两层：

### 9.1 Injection budget

- SessionStart 输出 ≤2500 bytes；
- breadcrumb 输出 ≤400 bytes；
- 只注入 stage/path/current sprint/next action/关键 pointers/阻塞；
- 平台能力表、发布日记、完整历史和遥测不自动注入；
- SessionStart 最多从 `_index` 追踪 3 个 allowlisted pointer，深度固定为 1；单个 pointer 文件最多读取 16 KiB，`_index` 最多读取 64 KiB；路径必须留在 `.ai_state/{sprints,roadmap,requirements,architecture,compound}/`；
- pointer 缺失、不可读、越界、路径逃逸或目标类型不符时输出有界诊断并 fail-open，不阻断普通提示；spec/delivery gate 的合同读取异常仍 fail-closed；
- UTF-8 预算按 bytes 计算，覆盖 startup/resume/clear 与 compact restore。

### 9.2 Retention policy

- `_index.md` 继续是唯一入口，不新增顶层状态文件；
- 每个活动 sprint 保留最近 3 个 pre-compact snapshot；同一 sprint 更旧的 snapshot 只在摘要成功后清理；
- ship 后 token/tool 原始遥测压缩为 sprint 统计摘要；
- 当前 release 与 N-1 release 保留可诊断摘要；更旧数据按 ship housekeeping 处理；
- consumer proof 是对 hook/skill/gate/setup 的 exact-path `rg` 清单 + 对应 runtime fixture，记录进 sprint retention evidence；
- 清理顺序固定为：同目录临时摘要 → parse/计数验证 → durable 原子 rename → 逐项删除已被摘要覆盖的 raw；任一删除失败即停止本批后续删除，保证已发布摘要和所有尚未删除 raw 保留，但不承诺恢复此前已成功删除的 raw；权限、并发、损坏或摘要写入失败时不开始删除；拿不到独占 cleanup lock 时跳过本次清理，不阻断 session；
- breadcrumb/restore 诊断 fail-open；spec-gate、delivery-gate 与权限边界 fail-closed。

## 10. Hooks

- 保留 SessionStart、stage breadcrumb、compact snapshot/restore、index updater、evidence、spec/delivery gate、subagent tracker 与 Stop reflection；
- 删除或合并重复叙述，不削弱 fail-closed 门禁；
- CC/CX hook 不要求事件逐一对称；
- Notification 只在 exact host 实测 payload 后配置；
- 不使用 `EndConversation` 代替 ship；
- Stop proposals 只记录具体、重复出现且有证据的演进建议，避免每轮制造文档噪声。

## 11. Local-only validation

本地脚本和 fixtures 不进入 Git。必须覆盖：

1. 9.9.3 baseline 与 9.9.6 相同场景；
2. CC exact 2.1.219 与当前 stable；`opus` 解析到 Opus 5；
3. CX exact 0.145.0 与当前 stable；CLI 与 App smoke；
4. ChatGPT login、OpenAI API Key 和 custom base URL preserve；
5. provider、multi-agent V2、role model/effort、skill invocation；
6. SessionStart/breadcrumb byte budget 与 cold-start bounded recovery；
7. 缺失/畸形/stale state、unknown evidence 与失败路径；
8. N9 token catalog audit、N10 artifact consistency；
9. fresh install、same-version、9.9.3 migrate/rollback；
10. `git status --porcelain` 不包含本地测试资产，且完整包含两个 release adapter。

完整 fork 证据不能只看 `git diff --stat`：B1 在任何迁移前生成排除 `.DS_Store`/cache 后的相对路径 + SHA-256 manifest，并证明 9.9.3→9.9.6 一致；B6 再做目标文件清单完整性比较、9.9.3 hash 不变与预期迁移 deny/allow scan。manifest 放临时目录，仅输出摘要，不进入 Git。

行为 eval 使用相同模型、effort、账户档位和 fixture，N≥3；正确性不得低于 9.9.3，效率改进使用 Pareto 判断。

## 12. Acceptance Criteria

- [ ] AC1: 9.9.3 两个目录零 diff；9.9.6 两个目录从其完整 fork，排除 `.DS_Store`/cache。
- [ ] AC2: CC adapter 不被 `.gitignore` 吞掉；`git status --porcelain` 可见完整底稿。
- [ ] AC3: CC 无 dated model pins、全局 subagent override、30s timeout/default-on noise；Opus 5 exact-version smoke 通过。
- [ ] AC4: CX 使用 built-in `openai`，无空 custom provider；保留 1M context、900K compact、Memories、warning 与用户态配置；省略 stable default-on flags 和冗余 skill 注册。
- [ ] AC5: WSL、`[desktop]`、plugins、App/CLI、ChatGPT/API Key 与 gateway preserve 合同存在并通过 smoke。
- [ ] AC6: Codex V2 配置职责符合 exact 0.145.0；不使用 V1-only `max_depth` 假装限制 V2。
- [ ] AC7: 双端 26 skills 可发现；受控 skill 自然语言不误触发、显式调用可用。
- [ ] AC8: PACE 4+5、红黄绿区、2+1 review、runtime-verify/polish 和 fail-closed gates 语义不退化。
- [ ] AC9: `.ai_state` 不新增第二状态层；SessionStart ≤2500 bytes、breadcrumb ≤400 bytes，恢复和异常场景通过。
- [ ] AC10: retention policy 有 consumer proof、N-1 边界与可回溯证据，不以磁盘大小粗暴删除。
- [ ] AC11: local-only 测试树符合用户指定路径且不在 Git diff；N9/N10、migration、rollback 全覆盖。
- [ ] AC12: prompt A/B N≥3，正确性不低于 9.9.3，至少一个效率指标 Pareto 改善。
- [ ] AC13: System design 至少两轮独立 critic 后 PASS；runtime-verify、2+1 review、polish、architecture 更新后才允许 ship。
- [ ] AC14: 未经用户后续授权，不 commit、push 或 release。
- [ ] AC15: CC `model=best` 且无全局 subagent override；architect/critic=Fable，其余五个角色=Opus；无 Sonnet agent 残留。

## Round 1 · Critic Findings

VERDICT: `NEEDS_REVISION`。

- 接受：旧设计错误引入 shared/contracts/renderer/runtime-capabilities；Codex floor 与 provider/V2/App 合同过期；skill invocation、N9/N10 与异常恢复不足。
- 修正 critic：测试目录按用户最终指定的扁平 `vibeCoding/scripts/`，不是旧 v3 的 `scripts/tests/`；CC `.gitignore` blocker 必须修复，不能因旧计划写了“不改 `.gitignore`”而忽略事实。

## Round 2 · Revision response

本版已删除第三层架构与第二状态层，恢复 exact 0.145.0 / Opus 5、endpoint-local contracts、用户指定目录、App/WSL/API 用户、skill invocation、AI-state injection+retention、N9/N10 和 fail-closed 边界。下一轮 critic 只评估本 v3.1 是否足以生成底稿，不重新打开用户已锁定的产品决策。

## Round 2 · Critic Findings

VERDICT: `NEEDS_REVISION`。

- 接受：底稿与最终 release 的依赖边界不清、Fable 删除需要原子 alias 迁移、checklist 缺 AC/dependency 映射、state recovery/retention 常量与失败语义不足。
- 修订：底稿 scope 与最终验收拆开；architect/critic provisional alias 冻结为 `opus`；恢复读取和 retention 常量、原子清理、并发及 fail-open/fail-closed 语义已明确。

## Round 3 · Revision response

本轮 generator 只执行 checklist 中 `B*` 底稿任务；`F*` 最终实现和 release 验收继续保持 pending。底稿允许应用已经由 exact source 与本设计冻结的原子配置迁移，但不得把未运行的 invocation/state/A-B 测试标绿。

## Round 3 · Critic Findings

VERDICT: `NEEDS_REVISION`。

- 接受：canonical roadmap 需明确映射 B1–B6；AC1 需规范化 manifest/content comparison；retention 不得承诺跨多文件删除的全事务回滚。

## Round 4 · Revision response

Canonical items 现在把 B1/B2 归 baseline/design 收尾，B3/B4/B5/B6 分别映射 Opus migration、platform contract、architecture freeze、reviewable bottom draft，并共享当前 sprint；状态由主 thread 串行推进。AC1 使用迁移前 SHA-256 manifest 证明完整 fork，retention 的部分删除保证已收窄为可实现语义。

## Round 4 · Critic Findings

VERDICT: `PASS`。无 P0/P1/P2 finding；B1–B6 roadmap 映射、完整 fork manifest、retention 部分删除语义及两份 YAML 一致性均通过。
