---
sprint_slug: "2026-07-25-athena-9-9-6-prompt-engineering"
path: "System"
created: "2026-07-25"
last_updated: "2026-07-27"   # §10.1 + AC16 增量 (Stop 阻断活锁熔断), 经 R5 critic 定稿
document_status: "critic-pass-ready-for-bottom-draft"
implementation_authorized: true
git_commit_authorized: true   # 用户 2026-07-27 显式授权 (AC14 满足)
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
- fresh package 的 `permissions.defaultMode` 使用官方规范值 `default`；Claude Code 2.1.200+ 也接受 `manual` 作为 `default` alias。迁移时不得覆盖用户已有的 `default` / `manual` / `acceptEdits` / `plan` / `auto` / `dontAsk` / `bypassPermissions` 选择。

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

Fresh `config.toml` 必须完全省略 `openai_base_url`。空字符串不是“使用官方默认”的表达，setup/validator 必须把该键存在且为空视为失败。

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
- Codex 0.145 的 function-tool hook 路径覆盖 `spawn_agent`，并兼容 `Agent` matcher alias；红区 spawn 在 PreToolUse 前置校验 worktree，SubagentStart audit 仅作事后证据与纵深防御。
- CC review 两个首轮 agent 不得由 frontmatter 强制后台；主线程必须收齐 reviewer/spec-compliance 返回后再启动 evaluator。

### 10.1 Stop 阻断活锁熔断 + 解锁动作正确化 (2026-07-27 追加, 实测驱动)

**起因 (实测, 非推测)**: `~/.codex/sessions/2026/07/26/rollout-...019f9ee2.jsonl` —— 一个在
`qc-wt-polish` worktree 跑 polish 的 CX exec 会话, **同一条阻断重复 286 次**
(14:46:34→15:26:45, 40 分钟, 平均 8 秒一次, 零进展):
`[delivery-gate] Refactor/System ship requires review-manifest.yaml (9.9.6 review contract)`

两个独立缺陷:

1. **解锁动作物理不可执行**。消费侧项目把 `stage` 置为 `ship` 时 Refactor 的 polish 尚未跑,
   随后把 polish 外包到 worktree。polish 改 `src/**` → `is_implementation_write` 判 true →
   走完整 ship 校验 → 撞 `review-manifest.yaml` 缺失。**而 manifest 是 polish 的下游产物,
   polish agent 永远造不出它**。gate 的判定没错 (状态确实不合法), 但报的是最末一个缺失文件,
   不是根因, 违反 doc-style 的 "block reason 必须含可执行解锁动作"。
2. **无重复阻断熔断器**。两端 `block()` 只吐 `{"decision":"block"}` 让模型重试, 无任何计数或升级。
   CC 侧 `stop-failure-recorder` 只记账不熔断, 且 **CX 侧根本没安装该 recorder** —— 尽管 CX gate
   已把 `stop-failures.jsonl` 列入漂移白名单, 等着一个不存在的写者。

**修法 (R1 critic 后定稿; 不削弱 fail-closed, 见下方"为何不是放水")**:

- **熔断只作用于 Stop 事件路径 (硬约束)**。CC 的 `continue:false` 在 CX 侧无从证实
  (codex 分发是 node shim, 原生二进制不在包内, 无法静态确证协议), 故熔断实现为:
  同因阻断连续第 N 次 (N=3) 起, gate **不再 emit `decision:block`**, 改为 exit 0 +
  stderr 打 `ESCALATED` + 追加升级记录。两端行为一致, 零协议押注。
  ⚠️ **熔断判定必须写在 Stop 分支内, 不得放进两端共用的 `block()`** (py:99 / cjs:995) ——
  否则同因重试的 **PreToolUse 实现写入第 3 次会被放行执行**, 那是 P0 越权。AC16f 是该约束的
  反向断言, 但正文在此明确, 不把唯一防线交给测试。
- **复用既有 `.ai_state/sprints/{slug}/stop-failures.jsonl`, 不新建文件** (R1-F4, 铁律[反过度工程])。
  该文件已存在、已在**两端** gate 的 `.ai_state` 漂移白名单内 (py:966 / cjs:470)、schema 自带
  `event` 判别字段, 可直接承载 `GateBlock` / `GateEscalated` / `GatePass` 三类记录。
  于是"新文件 + 两端白名单改动 + 对应 AC"三项整体消失, 4 处改动收敛为 2 处。
  记录字段: `event / ts / session_id / reason_sha1 / stage / path / consecutive`。
- **计数键 = `session_id + reason_sha1`** (R1-F2)。红区 Refactor/System **强制并行 worktree**,
  而 P3 修复后两端 gate 都解析主 repo 的 `.ai_state` (py:1293-1294 / cjs:1018-1019) ——
  多个并发会话必然追加同一 jsonl。只按 `reason_sha1` 计数会双向出错:
  (a) 会话 A 的 2 条 + 会话 B 的 1 条同因记录 → B 的**首个** Stop 即静默升级;
  (b) 两会话不同 reason 交替追加打断连续链 → **熔断永不触发**, 活锁恰在并行场景复活。
  CC/CX 的 Stop payload 均携带 `session_id`。追加一律 O_APPEND 单次 write
  (对齐铁律溯源待立条目"同事件多写者必须原子写")。30 分钟窗口保留, 作为 `session_id` 缺失时的兜底。
- **清零 = 一次"通过全部校验"的 Stop, 不是"未发 block"的 Stop** (R1-F1, 本轮最重要的修正)。
  原写法"任何一次非阻断 Stop 清零"是**自毁的**: escalated 的 Stop 本身就不发 block,
  按字面即刻清零 → 3 block + 1 escalate 无限循环, 活锁只降 25%。定稿:
  - `GateEscalated` 记录**计入尾链且不清零** —— 同因未解时后续 Stop 继续 escalate;
  - 清零由 gate 在**校验全过**的 Stop 上追加一条 `GatePass` 哨兵完成; 为避免每轮 turn 都写盘,
    **仅当本会话尾部记录是 `GateBlock`/`GateEscalated` 时才写哨兵** (无链可断时零成本);
  - 恢复阻断的条件因此只有两个: 状态真实变化 (reason_sha1 变) 或窗口过期。
- **解锁动作正确化**: ship 段对 Refactor/System, 在 manifest 检查**之前**先判 polish 产物
  `cleanup-pass.md`; 缺则报 "polish stage 未跑" + 真实解锁链 (跑 polish → 产出 cleanup-pass.md
  → 再补 review-manifest.yaml)。manifest 仍为必需项, 顺序不变, 只是先报根因。
  **空壳文件防护复用既有判据**: 沿用 `validate_meta_acceptance` 已有的 `PASS|completed|完成`
  内容判定 (py:601-603), 不引入新机制 (R1-F5a)。
  CX 侧 `block()` (py:99-103) 同时补上 CC 已有的解锁动作后缀 (cjs:996), 否则 AC16e 在 CX 无从满足。
- **N=3 的依据** (R1-F8, 原为拍脑袋): gate 的 reason 串内含状态细节 (如 checklist statuses 列表),
  **真实进展会改变 sha1 从而自动清零**, 故 N 只需覆盖"零状态变化的纯重试"。第 1 次告知、
  第 2 次证明上一次修复无效、第 3 次起零信息量 → N=3 = 留两次真实修复机会。N=2 过敏感
  (一次误操作即熔断), N≥4 只是拖延。原案例 8 秒一次的节奏下 ~24 秒触发。
- `stop-failures.jsonl` 的三类新记录须纳入 §9.2 retention/housekeeping (R1-F8)。

**为何不是放水 (必须成立, 否则本条作废)**: Stop 阻断唯一防的是"声称完成但无证据"。熔断后
①**无任何代码因此被合入** —— PreToolUse 实现写入门禁完全不变, ship 契约一条不减
(critic 已对着两端源码复核该路径, 未找到 P0 漏洞);
②**失败不被静默吞掉** —— 升级记录落盘, 且 SessionStart 须在下一会话 surface 未消解的升级 (AC16i);
③**熔断不改 gate 的判定** —— 只停止无意义重试; 状态真实变化或窗口过期后恢复正常阻断。
即"停止空转并交还人类", 不是"批准通过"。

**已知残余风险 (三条, 均留痕可审计)**:

1. agent 可故意连错 3 次后结束 turn 以避开 Stop 阻断的催逼。收益为零 (什么都没被批准),
   但会让"未完成"更易被搁置 → 由 ②的 SessionStart surface 兜底。
2. **外包 exec 会话的编排者不可见** (R1-F3, 本增量的原始场景正是这个形态): escalation 时
   stderr 不回喂被外包的会话, 其收尾消息是熔断前的中间状态, **可能仍声称完成**; 编排侧主 agent
   只读 final message, 看到的是一次干净 Stop。缓解 = **编排侧派发外包任务后必须检查
   `stop-failures.jsonl` 的 escalated 记录**, 不以外包会话的自述为准 (写入 pace skill 的外包段)。
3. ship 阶段 `.ai_state` 写入不受 PreToolUse 拦截 (P8 carve-out, py:1364 / cjs:1035), 且 reason 串
   确定、sha1 可预算 → agent 预写 3 条伪造记录即可让首个 Stop 静默升级 (R1-F6)。按 py:14 自陈的
   "workflow guardrail, not a security boundary" 定级, 不升 P; 采纳 `session_id` 计数键后伪造需
   匹配当前会话 id, 成本自然抬高; 兜底同 ②。

**本刀不处理但已记录**: `skip_polish` 在**两端均为死配置** (R1-F5b) —— 只出现在 governance
字段表 (py:871 / cjs:391), 无任何分支读取, `cleanup-pass.md` 对 Refactor/System 无条件必需
(py:1227 / cjs:972)。因它在 governance 哈希内, 改动会波及既有 manifest, 故**不在本刀扩面**;
现有 block 措辞对该配置为真的项目仍然准确 (gate 确实无条件要求 polish 产物)。列为独立待办。

**同族第三例 (2026-07-27 现场撞到, 独立待办)**: `MANIFEST_REQUIRED` 把 `evidence.yaml` 列为必需
哈希项, 而消费侧项目按"hook 运行日志不入 git"的正当理由把它 gitignore 掉
(quantum-cowork `.gitignore:28`, commit fe914b1)。该文件被 evidence-collector 每次 PostToolUse
追加 → 哈希必然漂移; 又不在 git 里 → **无任何来源可还原成 manifest 记录的哈希**;
重算 manifest 迁就它 = block 消息自己禁止的绕过。结果: 一个已 ship 并 push 的 sprint
**在往后每个新会话都卡死且无合法出路**, 只能走 idle 释放。
根治两选一: ①把 `evidence.yaml` 移出 `MANIFEST_REQUIRED` (它是运行日志, 本不该进治理哈希, 倾向此项)
②manifest 只对入 git 的文件计哈希, 遇 gitignored 文件显式跳过并标注。
判据沉淀: **进入治理哈希的文件必须同时 ①入 git ②不被 hook 自动改写**, 缺一即迟早死锁。
详见消费侧 `compound/2026-07-27-learning-manifest-pins-gitignored-file.md`。

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
11. 9.9.3 validator 的 package parity、install、F-series regression、runtime contract 与 fresh Codex 行为覆盖不得在 9.9.6 消失；覆盖按断言与 fixture 锁定，不按 `check_*` 函数数量锁定。
12. GPT-5.6 Sol/Terra 的 gateway dogfood 区分已复现的 Azure 0.144.0 问题与尚未证实的其他自定义 base URL，不把上游 issue 外推为所有网关必现。

完整 fork 证据不能只看 `git diff --stat`：B1 在任何迁移前生成排除 `.DS_Store`/cache 后的相对路径 + SHA-256 manifest，并证明 9.9.3→9.9.6 一致；B6 再做目标文件清单完整性比较、9.9.3 hash 不变与预期迁移 deny/allow scan。manifest 放临时目录，仅输出摘要，不进入 Git。

行为 eval 使用相同模型、effort、账户档位和 fixture，N≥3；正确性不得低于 9.9.3，效率改进使用 Pareto 判断。

## 12. Acceptance Criteria

- [ ] AC1: 9.9.3 两个目录零 diff；9.9.6 两个目录从其完整 fork，排除 `.DS_Store`/cache。
- [ ] AC2: CC adapter 不被 `.gitignore` 吞掉；`git status --porcelain` 可见完整底稿。
- [ ] AC3: CC 无 dated model pins、全局 subagent override、30s timeout/default-on noise；Opus 5 exact-version smoke 通过。
- [ ] AC4: CX 使用 built-in `openai`，fresh config 不含 `openai_base_url` 或空 custom provider；保留 1M context、900K compact、Memories、warning 与用户态配置；省略 stable default-on flags 和冗余 skill 注册。
- [ ] AC5: WSL、`[desktop]`、plugins、App/CLI、ChatGPT/API Key 与 gateway preserve 合同存在并通过 smoke。
- [ ] AC6: Codex V2 配置职责符合 exact 0.145.0；不使用 V1-only `max_depth` 假装限制 V2。
- [ ] AC7: 双端 26 skills 可发现；受控 skill 自然语言不误触发、显式调用可用。
- [ ] AC8: PACE 4+5、红黄绿区、前台收齐的 2+1 review、CX spawn 前置 worktree 门禁、runtime-verify/polish 和 fail-closed gates 语义不退化。
- [ ] AC9: `.ai_state` 不新增第二状态层；SessionStart ≤2500 bytes、breadcrumb ≤400 bytes，恢复和异常场景通过。
- [ ] AC10: retention policy 有 consumer proof、N-1 边界与可回溯证据，不以磁盘大小粗暴删除。
- [ ] AC11: local-only 测试树符合用户指定路径且不在 Git diff；N9/N10、migration、rollback 全覆盖。
- [ ] AC12: prompt A/B N≥3，正确性不低于 9.9.3，至少一个效率指标 Pareto 改善。
- [ ] AC13: System design 至少两轮独立 critic 后 PASS；runtime-verify、2+1 review、polish、architecture 更新后才允许 ship。
- [ ] AC14: 未经用户后续授权，不 commit、push 或 release。
- [ ] AC15: CC `model=best` 且无全局 subagent override；architect/critic=Fable，其余五个角色=Opus；无 Sonnet agent 残留。
- [ ] AC16: Stop 阻断熔断与解锁动作正确化 (§10.1)，双端行为一致，且 PreToolUse 实现写入门禁零削弱。逐项可证伪：
  - [ ] AC16a: 构造同因阻断连发，第 3 次起 gate 不再 emit `decision:block`，改 exit 0 + stderr `ESCALATED`；前 2 次仍正常阻断。
  - [ ] AC16b: 每次阻断在 `.ai_state/sprints/{slug}/stop-failures.jsonl` 追加一条 `event:"GateBlock"` 且含 `session_id`/`reason_sha1`/`consecutive` 的记录；**一次校验全过的 Stop** 写入 `GatePass` 哨兵后计数清零，下一次同因阻断从 1 重新计。
  - [ ] AC16b2 (R1-F1 反向断言): `GateEscalated` 记录**不清零** —— 连续 ≥6 次同因 Stop 中，第 4/5/6 次全部继续 escalate，不得回落成 "block, block, escalate" 的循环。
  - [ ] AC16c: 尾部同 hash 但**超出 30 分钟窗口**的记录不计入连续数；另需**并发双会话 fixture** (R1-F2): 会话 A 已有 2 条同因记录时，会话 B 的首个 Stop 仍正常阻断 (不被 A 的计数带进升级)，且 A/B 不同 reason 交替追加不打断各自连续链。
  - [ ] AC16e: Refactor/System 在 ship 段缺 `cleanup-pass.md` 时，block reason 报 "polish stage 未跑" 且含完整解锁链；补上 `cleanup-pass.md` 后才改报缺 `review-manifest.yaml`（顺序回归：manifest 仍为必需项，未被降级）。空壳 `cleanup-pass.md` (无 `PASS|completed|完成`) 仍判为未跑。
  - [ ] AC16f: 熔断只作用于 Stop 路径 —— PreToolUse 实现写入在连发 N 次后**仍然逐次阻断**，不得被熔断放行 (反向断言，防越权)；且 **PreToolUse 阻断不推进 Stop 计数器** (R1-F7: 否则 3 次写入被拦后首个 Stop 即升级，AC16a 对该会话失效)。
  - [ ] AC16h: 复现原始活锁场景 (stage=ship + Refactor + 无 manifest + polish 写 `src/**`)，**连续 ≥12 次 Stop 尝试中 `decision:block` 发射总数 ≤3** (R1-F7: 钉重放长度，防 4 次迭代的偷懒测试在错误清零语义下假绿)。
  - [ ] AC16i (R1-F3): SessionStart 在存在未消解 `GateEscalated` 记录时输出含 `ESCALATED` 的诊断行，且注入总量仍 ≤2500 bytes (对齐 §9.1 合同)。这是"不是放水"论证②的承重腿，必须有验收。

> **拆出，不与 AC16 捆绑** (R1-F4): CX 侧补装 `stop-failure-recorder.py` 与活锁修复**无因果关系**
> (熔断记录由 gate 自己写)，属搭车项。列为独立小项验收: 存在且非阻断、路径与字段同 CC `.cjs`、密钥脱敏。

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


## Round 5 · Critic Findings (§10.1 + AC16 增量, critic=Fable 5, 2026-07-27)

> 范围: 仅评审 2026-07-27 追加的 §10.1 与 AC16 增量。AC1-AC15 与 §1-§10 是已过 R1-R4 的既有设计, 不在本轮。
> 起因: Codex exec 会话实测活锁 290 次 (证据见 §10.1 首段, rollout jsonl 可复核)。

VERDICT = **APPROVE_WITH_CHANGES**
评分: 边界条件 3 · 错误处理 4 · 可证伪性 3 · 过度设计 3 · 历史教训对齐 4

critic 对着两端 gate 源码复核了"熔断是否削弱 fail-closed": **未找到 P0 路径**, PreToolUse 的
block 路径与 ship 契约一条不减 —— 但**前提是熔断判定不放进共用的 `block()`**, 该约束已升为 §10.1 正文硬约束。

| # | Sev | 问题 | 处置 |
|---|---|---|---|
| F1 | P1 | **清零语义自毁**: escalated 的 Stop 本身即"非阻断 Stop", 按原文字面即刻清零 → 3 block + 1 escalate 无限循环, 活锁只降 25%; 且"下一 turn 重新阻断"与窗口机制自相矛盾 | ✅ 定稿: 清零 = 校验全过的 Stop + `GatePass` 哨兵; `GateEscalated` 计入尾链不清零; 论证③重写。补 AC16b2 反向断言 |
| F2 | P1 | **并发 worktree 共用同一 ledger**: 红区强制并行 worktree 而两端 gate 均解析主 repo `.ai_state`, 只按 `reason_sha1` 计数 → (a) 会话 B 首个 Stop 即静默升级 (b) 交替 reason 打断连续链使熔断**永不触发**, 活锁恰在并行场景复活 | ✅ 计数键改 `session_id + reason_sha1`; O_APPEND 原子追加; AC16c 补并发双会话 fixture |
| F3 | P1 | **"不是放水"论证②无验收覆盖**; 更深: 外包 exec 会话 escalation 时 stderr 不回喂, 编排侧只读 final message → 看到的是一次干净 Stop, 而该会话可能仍声称完成 | ✅ 补 AC16i (SessionStart surface + ≤2500 bytes); 残余风险节新增第 2 条并给编排侧缓解动作 |
| F4 | P1 | **反过度工程**: `stop-failures.jsonl` 已存在、已在两端白名单、schema 自带 `event` 判别字段, 复用即可让新文件/AC16d/两端白名单改动整体消失 (4 处 → 2 处); AC16g 的 CX recorder 与活锁修复无因果, 是搭车项 | ✅ 全采纳: 改用 `stop-failures.jsonl`, 删 AC16d; AC16g 拆为独立小项 |
| F5 | P2 | (a) 空壳 `cleanup-pass.md` 一行 stub 即过存在性判定 (b) **`skip_polish` 在两端均为死配置** —— 只在 governance 表出现, 无分支读取 | ✅ (a) 复用 `validate_meta_acceptance` 既有 `PASS\|completed\|完成` 判据, 零新机制; (b) 因在 governance 哈希内改动波及既有 manifest, **本刀不扩面**, 记为独立待办 |
| F6 | P2 | 计数文件反向驱动 gate 行为且 agent 可预写伪造记录 (ship 段 `.ai_state` 写入不受 PreToolUse 拦) | ✅ 按 py:14 自陈 "workflow guardrail, not a security boundary" 不升 P; 入残余风险第 3 条; `session_id` 键使伪造成本抬高 |
| F7 | P2 | AC16h 未钉重放长度 (4 次迭代的测试在错误清零语义下也全绿); AC16f 未断言 PreToolUse 阻断**不推进** Stop 计数 | ✅ AC16h 钉 "≥12 次 Stop 尝试, block 发射 ≤3"; AC16f 补该子断言 |
| F8 | P3 | N=3 无书面依据; 新记录未入 §9.2 retention; CX `block()` 缺 CC 已有的解锁动作后缀 | ✅ 三项均补入 §10.1 |

**critic 对"有无更简修法"的回答**: 只修 block reason **不够** —— polish agent 即便被正确指引产出
`cleanup-pass.md`, 下一个 manifest 阻断它仍造不出 (manifest 是 review 下游产物), 活锁会在第二个
reason 上复发。熔断本身必要; 但四处改动可收敛为两处 (F4 已采纳)。
