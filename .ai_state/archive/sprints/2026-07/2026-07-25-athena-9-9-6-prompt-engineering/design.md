---
sprint_slug: "2026-07-25-athena-9-9-6-prompt-engineering"
path: "System"
created: "2026-07-25"
last_updated: "2026-07-28"   # 用户关闭该方向
document_status: "closed-by-user-no-release-claim"
implementation_authorized: false
git_commit_authorized: false
roadmap_slug: "athena-9-9-6-prompt-engineering"
baseline_release: "9.9.3"
target_release: "9.9.6"
---

# Design — Athena 9.9.6 Prompt Architecture v3.1

> Closure (2026-07-28): 用户决定停止本路线。原本的改动反复且叙述冗长，后续不再考虑同类扩展；本设计保留为历史记录，不代表最终 release 已完成。

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

## 12. Gate 契约可见性与派工时序 (2026-07-28 追加范围)

> 完整论证、逐条源码行号锚点、备选方案对比与风险表见同目录 `annex-2026-07-27-gate-contract.md`
> (原独立 sprint design, 用户 2026-07-28 拍板并入本 sprint 作追加范围)。本节是压缩版契约。
>
> **判据原则**: **门禁的判据必须在它所约束的文档模板里可见, 否则就是隐藏考纲。**
> 八条失败全部追溯到消费侧 `quantum-cowork` 2026-07-27 `ledger-debt-batch` sprint 的实测,
> 其中两个 worktree 写者整轮撞墙、约 21 万 token 花在被阻断的运行上。

**本刀边界: 只改文档面 (模板 + rules + references), 两端 `delivery-gate.cjs`/`.py`、evidence-collector
与任何 hook 一行不动。** hook 侧机械化 (A 的 block 消息增强、B-m1 spawn 关口拦截、critic 计数锚定到标题行)
列为下刀候选, 起因与判据已在 annex 留痕。

### 12.1 A · 把 delivery-gate 的机器契约写进它所约束的模板

契约事实 (2026-07-27 逐条对源码核实, 锚点用函数/常量名, 行号为辅):

1. `ACCEPTANCE_HEAD` 只认 `## Acceptance Criteria` / `## 验收标准` (2-3 级标题), 序号前缀只允许
   ASCII `\d+[.)]` —— CJK 序数 `## 六、验收标准` 不匹配, 解析结果 0 条。
2. `acceptanceCriteria()` 节内只收列表项 (`-` / `*` / `\d+.` / `[ ]`), **markdown 表格行一条都不算**;
   占位符与泛化陈述被 `isPlaceholderCriterion` 剔除。
3. `validateCriticRounds` 数的是 design.md 里**字面** `Critic` + 空格 + `Findings` 的**全文出现次数**
   (无位置约束), Refactor/System 地板 = 2 —— 段头必须逐字保留, **改写一个段头就少计一轮**
   (不是清零, R6-F7 校正)。双向失真: 正文讨论该契约会**虚增** (§12.7-1),
   而模板 scaffold 自带的段头让每个新 sprint **起算即 1** (§12.7-4, R6-F2 实测)。
4. **编号 11/12 是 harness 保留元标号**: `validateMetaAcceptance` 命中 11 号要求 evaluator
   VERDICT=PASS, 命中 12 号要求 cleanup 证据 + 活动 worktree 数 = 1; 且 `validateAcMapping`
   把这两个标号**排除在 per-AC 绑定校验之外**。排除本身有正当理由 (给元 AC 造 evidence 行是循环论证),
   缺陷在**保留语义任何模板都没写**, 业务 AC 占用即静默免检。**本 sprint 自己踩中**: 原 AC11/AC12
   是业务 AC, 已按本条重编号为 AC17/AC18 (见 §13 表头注)。
5. `validateAcMapping` 只认 `evidence.yaml` 记录里的 `ac_id` / `covers`, admissible 三形态为
   `source: command` (要 output_artifact + sha256 + exit 0 + implementation_commit 绑 reviewedCommit)
   / `source: artifact` / `source: review` (指向含 `## Spec Compliance` + `## Evidence Cross-Check`
   + 逐 AC SATISFIED 行 + VERDICT PASS 的最新 review)。**hook 自动采集的记录没有这两个字段**
   (evidence-collector 不写); 写者交的 `tdd-evidence.yaml` 走另一条校验, **不参与 AC 绑定**。
   该校验仅在 `review-manifest.yaml` 存在时执行, 而 Refactor/System 的 manifest 是强制的 ——
   **红区必踩, 非红区则业务 AC 完全不绑定证据, 同一份 AC 在两条路径下强制力差一整级**。

修法 (双端对称, 全部文档面):

- **A1 模板注记块**: 两端 `skills/pace/templates/sprints/design.md` 的验收标准节上方加「⚙ 机器契约
  (delivery-gate 同步)」引用块, ≤20 行, 覆盖上述五要素, 每要素附函数/常量名锚点, 尾行标同步日期。
  模板既有骨架本身合规, **不改骨架** —— 修的是消费者重写骨架时零警示这个可见性缺陷。
- **A2 stages.md ship 段**: 新增 per-AC 绑定记录义务 —— review PASS 后、翻 ship 前, 主 agent 为每条
  业务 ACn 向 `evidence.yaml` 追加绑定记录 (最低成本形态 = `source: review` 指向最新 passN),
  附 admissible 三形态速查与「hook 自动采集记录不构成绑定」的显式警示。
- **落点权衡**: 不改采集器 (它不可能知道一条命令覆盖哪条 AC, 自动补 `covers` = 机器替人签名 = 伪造绑定,
  违反铁律[证据与出处]); 不放宽 hook (会把三形态中最强的 sha256/commit 锚定形态边缘化)。
  绑定必须是**有意为之的断言** —— 谁声称这条命令/审查覆盖了 ACn, 谁签名。

### 12.2 B · stage 翻转时序规则

事实: delivery-gate 挂 PreToolUse `Edit|Write|MultiEdit` + Stop; P3 修复后从**主 checkout** 解析
`_index.md`, 故 worktree 里的写者同样受主仓 stage 支配, 门禁从翻转那一刻起对所有在飞写者即时生效。
消费侧当天三个写者开工后 stage 才翻 impl, 全部锁死。

规则文本 (落 references, **不进 CLAUDE.md 铁律** —— stages.md 是 stage 义务真相, 且 CLAUDE.md
受常驻预算约束):

> stage 进 impl (含 `current_sprint_slug` 切换) 必须在**首次派工之前**完成;
> 派工前主 agent 必须自检本 sprint design 的 AC 段可被 gate 解析 (见模板机器契约块);
> 存在在飞写者 (`active_worktrees` 非空, 或 subagent-events 有未配对 Start) 时,
> 不得修改 `_index` 的 `stage` / `current_sprint_slug`。

落点: 两端 `stages.md` impl 工作流新增 step 0; `orchestration.md`「worktree 规则速查」追加同义一条。

### 12.3 C · 共享「已验证基线」载体

事实: 同一组基线被 5 个独立主体从零重测。**复核本身是对的** —— 正是复核推翻了 critic R1 建议的判据
(实测命中 0 行) 和主 agent 自己的 AC 判据 (未修代码上恒绿)。**设计目标 = 降低复核成本, 不是取消复核。**

修法: 两端 `pace/templates/sprints/route-note.md` 新增「已验证基线」五列表格节 (事实 / 测量命令
(单条可复跑) / 实测值 / 测于 commit 或时刻 / 已复核方), 派工契约随附该节 (orchestration.md 派工段注明)。
边界必须写死:

> 写者对自己依赖的每条基线**必须复跑所附命令核对** (一条命令, 而非从零推导); 不一致 → 立即停下上报,
> 两个值都留档。**不得退化为采信不复核** —— 无测量命令的基线条目视同未验证, 不得作为 AC 或裁决依据。

### 12.4 D · 类型不可见依赖进 review 检查单

事实: critic 判「纯重构可做到测试零修改」用的检索式抓不到 `(x as unknown as { tools: T }).tools`
这类私有字段访问 —— 它对 `tsc --noEmit` 隐形 (运行时形状改了仍 EXIT=0), 对 import 分析也隐形。

> **原则句: 可达性论证所用的检索式, 必须能抓住该 AC 自己要防的那类失败。**

修法: 三份 `coding-standards.md` (USER 级 + 两端发行件) 的 review 段新增 P1 检查项 —— 声称
「纯重构 / 测试零修改 / 无外部消费者」前, 检索式至少覆盖 `as unknown as` · `as any` ·
对私有/内部字段的运行时访问 (含索引访问与 `.db` 式内部读) · prototype 打桩 · 动态 require/import。
清单是下限不是上限, 原则句兜底。

### 12.5 E · 量化 AC 写绝对值而非 `≥`

事实: `≥1966` 在三写者并行时允许「一片删测试、另一片加测试」互相抵消; 改为绝对相等 + 构成式后,
合并实测 1976 与构成式吻合。

修法: 三份 `doc-style.md` 新增「量化 AC 记法」—— 并行多写者场景的计数类 AC 必须写**绝对相等 + 构成式**
(基线 + 各片增量 = 总量), 禁 `≥`; 单写者可用下界, 但基线值必须附测量命令与出处 (与 12.3 基线节、
coding-standards「量化验收标准必先核基线」互为引用)。

### 12.6 F · batch/debt 路径 (只记录, **待用户拍板, 本刀零实施**)

Refactor 地板 = critic ×2 + 3 写者 + 2+1 review ≈ 9 次冷启动 subagent, 对「六项互不相干的小债」是超配。
但 **critic 不可削**: 两轮 18 条 findings 含 3 条 P0, 其中「验收判据在未修代码上恒绿」若漏掉整片就是假绿。
三案: F-a 维持现状 (批次按最重切片取路径地板) · F-b 新增 batch/debt 档 (一次分诊 + 一份 design +
各片单写者 + 合并后一次 2+1 review; 机械边界 = 各片文件面互不相交、单片 ≤10 文件、跨片 AC 显式署名) ·
F-c 逐片走 Feature 挂同一 roadmap。annex 撰写者推荐 F-b。**未拍板前一切照 F-a 执行**, AC26 是反向断言。

### 12.7 已知脆弱性 (留痕, 不在本刀扩面)

1. **critic 轮次字面计数可被正文讨论污染**: `validateCriticRounds` 全文匹配, 任何**讨论**该契约的
   design (含本节、含 A1 修后的模板注记块) 都可能虚增计数 → 检查被平凡满足。本节与 annex 均以转写规避。
   根治 = 计数锚定到 2-3 级标题行内出现该字面串, 属 hook 改动, 记 proposals 待下刀。
2. **LOCAL-PATCHES 快照漂移**: `vibeCoding/claude/9.9.6/hooks/delivery-gate.cjs` 入库快照 (2026-07-26)
   已落后于 `.claude/hooks/` 发行件与安装态 (2026-07-27 熔断器 + manifest gitignore 修复未同步),
   而 LOCAL-PATCHES.md 仍声称「与安装态逐字节一致」。AC28 要求实施时刷新或显式登记不刷新理由。
3. **模板注记块随 gate 演进过期**: 契约写两处必漂。缓解 = 以函数/常量名为锚 + 尾行标同步日期 +
   把「gate 判据变更须同步模板注记」写进注记块自身; 根治 (契约单源生成) 超出本刀, 记 proposals。
4. **模板 scaffold 自带幻影 critic 轮次** (R6-F2 发现, 主 agent 复核确认): 两端安装态与两端发行件的
   `pace/templates/sprints/design.md` **`:72` 均含一行 Round 1 scaffold 段头**, 其中原样带有该字面串
   (本档为免污染自身计数, 不复写该行原文; 复核用 `sed -n '72p' <模板>`)
   —— 四份 `grep -c` 全部 = 1。任何由模板实例化的 sprint **起算即 1 轮**, Refactor/System 地板 2
   于是只强制**1 轮真实审议**, Feature 地板 1 更是零。这不是本 sprint 的局部问题, 是**全体消费方的
   ratchet 侵蚀**, 且与 §12 要治的"考纲失真"同源。本刀顺 A1 之刀改 scaffold 段头为转写占位
   (仍是文档面, "不改骨架"约束指的是 AC 节骨架), 核验并入 AC19 第 ② 条。

## 13. Acceptance Criteria

> **编号约定 (2026-07-28)**: 编号 **11/12 是 harness 保留元标号**, 业务 AC 一律避开 (见 §12.1 第 4 条)。
> 原 AC11 → **AC17**, 原 AC12 → **AC18** (checklist.yaml 的 `ac_refs` 已同步)。
> §12 追加范围的验收为 **AC19-AC28**, 与 annex 原 AC1-AC10 按序一一对应。
>
> **重编号的净效果 = 加严一处 + 失守一处 (R6-F1 核出, 不是纯加严)**:
> ①**加严**: AC17/AC18 从 `validateAcMapping` 的静默免检名单里挪出来了, ship 时必须交
> admissible per-AC PASS evidence。②**失守**: 标号集不再含 11/12 → `validateMetaAcceptance`
> (cjs:852-867/py:730-744) 永不触发。其中 evaluator VERDICT=PASS 半边由 `validateReview`
> (cjs:291/py:912-913) 对全部 generator 路径无条件强制、cleanup 半边由 ship 前置判
> (cjs:957-967/1000) 覆盖, **均零损失**; 但 **"ship 时活动 worktree 计数 = 1" 这一谓词全 gate
> 仅此一处** (`rg 'worktree list --porcelain'` 两端各 1 命中, 均在该函数内), 重编号后无人执行
> → 由 **AC28a** 以 `source: command` 证据人工补回。
>
> **条目正文内禁写其他 AC 编号**: 标号抽取扫的是条目正文 (cjs:810/py:401,
> 形如 `(?:^|[^A-Za-z0-9])(AC\d+)(?![0-9])` —— 前有非字母数字边界、后不接数字), 在 AC17 正文写
> "(原 AC11)" 会把保留标号重新注射进标号集, 使重编号失效。映射一律只写在本表头注里。

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

- [ ] AC17: local-only 测试树符合用户指定路径且不在 Git diff；N9/N10、migration、rollback 全覆盖。
- [ ] AC18: prompt A/B N≥3，正确性不低于 9.9.3，至少一个效率指标 Pareto 改善。

<!-- 以下 AC19-AC28 为 2026-07-28 追加范围 (§12), 与 annex 原 AC1-AC10 按序对应。
     编号映射与"条目正文禁写其他 AC 编号"的理由见本节表头注, 此处不重复
     (契约写两处必漂, §12.7-3)。 -->

- [ ] AC19: CC/CX 两份 design 模板的验收标准节上方各有一个 ≤20 行的机器契约注记块，覆盖五要素（标题白名单+ASCII 序号 / 仅列表项 / 保留元标号语义与业务 AC 避让 / critic 字面计数 / evidence 绑定义务含红区与非红区强制力分级）。**机械核验三条**（R6-F4：不接受"人工比对"式软验收）：① 五个 gate 锚点 token 在每份模板各 `rg -c` ≥1 —— `ACCEPTANCE_HEAD`、`isPlaceholderCriterion`、`validateCriticRounds`、`validateMetaAcceptance`、`validateAcMapping`；② 注记块**自身**对 critic 计数字面串一律转写，`grep -c` 该字面串在每份模板 **= 0**（R6-F2：包括必须顺刀改掉的既有 Round 1 scaffold 段头）；③ 注记块引用的标号抽取正则须与 cjs:810/py:401 实际判据一致（带前界 + 后禁数字），不得写成过度简化的形式（R6-F7）。
- [ ] AC20: 红绿对照实测 —— /tmp fixture 项目，红绿**共用同一 fixture 仅替换 design.md**，用 `node ~/.claude/hooks/delivery-gate.cjs` 喂 PreToolUse 实现写入 payload。四条防假绿钉死（R6-F3）：① fixture `_index.md` 的 `path` 取 **Refactor**（path ∉ Feature/Refactor/System 时 `validateImplEntry` 直接 return，绿例会平凡通过）；② payload 的 `cwd` = fixture 根，`file_path` 指向 fixture 内**非 `.ai_state/`** 的实现文件（否则 quiet-exit 同样平凡通过）；③ 绿例（按改后模板骨架填一条真 AC）**无 `decision:block`**；④ 红例（复现 `## 六、验收标准` + 表格行形态）不仅要 block，**reason 须含"缺机器可识别的验收标准段"**。两次完整输出留档进本 sprint evidence。
- [ ] AC21: CC/CX 两份 stages.md 的 ship 段含 per-AC 绑定记录义务（触发条件、admissible 三形态速查、`source: review` 最低成本路径、hook 自动采集记录不构成绑定的警示）；核验 = `rg -n "ac_id|covers" <两份 stages.md>` ≥1 且义务段完整。
- [ ] AC22: CC/CX 两份 stages.md 的 impl 工作流含 step 0 派工时序规则（翻 stage 先于派工 + 派工前 AC 段自检 + 在飞写者存在时禁改 stage/current_sprint_slug），orchestration.md worktree 速查含同义条目；核验 = `rg -n "派工" <三档>` 命中对应句。**自检形态钉死（R6-F6）**：写进 stages.md 的自检**必须**是"合成一个 PreToolUse payload 喂安装态 gate 本体、期待无 `decision:block`"（与 AC20 fixture 同源），**禁止**给出手搓正则复刻 gate 判据的命令 —— 那是 §12.7-3 双写漂移的新实例。
- [ ] AC23: CC/CX 两份 route-note 模板含「已验证基线」五列表格节，orchestration.md 派工段注明随契约下传；边界句逐字含「不得退化为采信不复核」与「无测量命令的基线条目视同未验证」。
- [ ] AC24: 三份 coding-standards（USER 级 + CC/CX 发行件）的 review 检查项含类型不可见依赖检索清单（至少 `as unknown as` / `as any` / 私有字段运行时访问 / prototype 打桩 / 动态导入 五类）与「检索式必须能抓住该 AC 自己要防的那类失败」原则句及出处引用。
- [ ] AC25: 三份 doc-style（USER 级 + CC/CX 发行件）含量化 AC 记法（并行多写者 = 绝对相等 + 构成式、禁 `≥`；单写者下界须附基线测量命令与出处），并交叉引用 §12.3 的基线节。
- [ ] AC26 (反向断言): F 条保持「待用户拍板」形态 —— 本 sprint 的 git diff 不含任何 batch/debt 路径的 skill/hook/模板实现；核验 = diff 审读。
- [ ] AC27: 双端对称性 —— 每处 CC 改动有 CX 对应落点，或**在 annex §四影响范围表**显式登记不对称原因（R6-F4：§12 无影响范围小节，登记归宿是 annex 那张表）；登记行须含**双端路径 + 一句语义映射**，不得只写"CX 无对应"（CC/CX 只对齐语义，不伪造对称）；核验 = 对照该表逐行检查。
- [ ] AC28: 安装态与 Rlues 发行件双写一致（逐文件 `diff` 空），且 `harness-patches.md` 为本刀每处安装态改动新增带复核命令的台账行；§12.7 第 2 条的 LOCAL-PATCHES 快照漂移已刷新或已登记不刷新理由；2026-07-28 复核记录中标记失真的三条期望值（W3/W8/W9）已按"复核命令必须锚定到被修的那一处"修正。
  - [ ] AC28a（R6-F1 补回失守谓词）: ship 前实跑 `git worktree list --porcelain` 并断言活动 worktree 计数 = 1，输出以 `source: command` 形态留档绑定本 AC。理由与出处见本节表头注「失守」段（该谓词全 gate 仅存在于 `validateMetaAcceptance`，cjs:864-866/py:741-744）——用一条人工证据补回，不动 gate。

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


## Round 6 · Critic Findings (§12 + AC19-AC28 追加范围, critic=Fable 5, 2026-07-28)

> 范围: 仅评审 2026-07-28 追加的 §12 全节、§13 AC19-AC28 与 AC 重编号 (17/18)、checklist G1-G6/H1
> 与 done_contract 三条、route-note `## 2026-07-28` 节。§1-§11 与 AC1-AC18 既有设计不重开。
> §12.1 五条契约事实已逐条对安装态 cjs/py 源码亲验 **一致** (锚点: ACCEPTANCE_HEAD cjs:613/py:395 ·
> acceptanceCriteria cjs:626-641 · validateCriticRounds cjs:602,605/py:1389-1396 · 元标号排除
> cjs:813/py:667 与 validateMetaAcceptance cjs:852-867/py:730-744 · validateAcMapping 三形态
> cjs:819-844 + manifest 触发 cjs:984-990/py:1579-1604)。字面串计数实测 = 5, 全在 R1-R5 段头,
> 本次追加文字零污染; checklist 与 AC 段均无 11/12 残留; §12.7-2 快照漂移属实; G6→F7 依赖正确;
> F 条零实施形态正确。

VERDICT = **APPROVE_WITH_CHANGES**
评分: 边界条件 4 · 错误处理 4 · 可证伪性 3 · 过度设计 4 · 历史教训对齐 5

| # | Sev | 问题 | 处置 |
|---|---|---|---|
| F1 | P1 | **"重编号是加严"不完全成立, 有一条检查净丢失**。元校验的 evaluator VERDICT=PASS 半边由 `validateReview` 对全部 generator 路径无条件强制 (cjs:291/py:912-913), cleanup 半边由 ship 前置判 (cjs:957-967, cjs:1000/py:1553-1562) 覆盖, 均零损失; 但 **"ship 时活动 worktree 计数=1" 全 gate 仅存在于 `validateMetaAcceptance`** (cjs:864-866/py:744), 重编号后 labels 不含 11/12 → 该谓词永不触发, AC13/G6 均未覆盖 | ✅ 主 agent 复核确认成立 (`rg 'worktree list --porcelain'` 两端各仅 1 处, 均在该函数内)。§13 表头注已改口为"加严 + 一处失守"; AC28 增子项 AC28a 以 `source: command` 证据补回该谓词 |
| F2 | P1 | **G1 要改的模板自带 1 次幻影轮次**。两端安装态 + 两端发行件 design 模板 `:72` 的 Round 1 scaffold 段头含该字面串 → 实例化即起算 1, Refactor/System 地板 2 实际只强制 1 轮真实审议 —— 正是 §12 要治的"考纲失真"同类, 且 §12.7-1 只防了注记块, 未防既有 scaffold | ✅ 主 agent 复核确认成立 (四份模板 `grep -c` 均 = 1, 命中 `:72`)。A1 顺刀改 scaffold 段头为转写占位; AC19 增核验"模板内该字面串出现次数 = 0"; 注记块须转写的约束从 §12.7-1 升格绑进 AC19 |
| F3 | P2 | **AC20 假绿路径未钉死**: (a) fixture `_index.md` 的 path 必须 ∈ Feature/Refactor/System, 否则 `validateImplEntry` 直接 return (cjs:871-876); (b) payload 须带 cwd=fixture 根、写入路径不含 `.ai_state/` (cjs:1016-1020), 否则 quiet-exit 使绿例平凡通过; (c) 仅断言有/无 `decision:block` 不够 | ✅ AC20 已补四钉: path 取 Refactor · 红绿共用同一 fixture 仅换 design.md · 红例断言 reason 含"缺机器可识别的验收标准段" · payload cwd 与文件路径显式给定 |
| F4 | P2 | **软验收两处**: AC19"人工比对五要素"不可机械证伪; AC27 让不对称原因登记进"§12 影响范围", 但 §12 无影响范围小节 (表在 annex §四, 而 annex 自声明不参与机械校验) | ✅ AC19 改为五锚点 token 各 `rg -c` ≥1; AC27 改指 annex §四并要求登记行含双端路径 + 一句语义映射 |
| F5 | P2 | **台账时序陷阱**: `harness-patches.md` 是 git 跟踪文件, 不在 `validateReviewBinding` 漂移白名单 (cjs:471-491) 且永判非轻 (cjs:889/py:1188) —— review 绑定 commit 之后再补一笔台账即"unreviewed .ai_state drift"卡死 ship | ✅ G6 `expected_evidence` 补排序约束: 台账收口 → 进 reviewed commit → 冻结; review 期间新增安装态改动须重走绑定 |
| F6 | P2 | AC22 的"派工前 AC 段自检命令"未定义形态; 手搓正则复刻品 = §12.7-3 双写漂移的新实例 | ✅ AC22 钉死: 自检 = 合成 PreToolUse payload 喂**安装态 gate 本体**、期待无 `decision:block` (与 AC20 fixture 同源), 禁正则复刻 |
| F7 | P3 | 将被抄进 A1 注记块的两处措辞欠精确: "改写段头即清零"实为逐个少计; §13 注释引 `matchAll(/(AC\d+)/g)` 与实际判据 (cjs:810/py:401, 带前界 + 后禁数字) 不同 (方向为过度警示, 无危险) | ✅ §12.1 第 3 条与 §13 注释均已改用准确表述; 注记块抄实际正则 (并入 AC19) |
| F8 | P3 | G2-G5 串行 `blocked_by` 链含假依赖 (G4 不真依赖 G3), 单写者策略下无害; done_contract"本刀零 hook 改动"仅靠上行注释限定范围, 与本 sprint 已落的 fe3296d 熔断器改动字面相抵 | ✅ done_contract 该行行内自带"(§12 G 系列)"限定; 假依赖留痕不改 (单写者串行下无害, 改动收益 < 扰动风险) |

**critic 对"有无更简修法"的回答**: 整体无 —— "只动文档面、hook 一行不动"已是本问题的最小正确刀位
(亲验确认放宽 hook 或改采集器的否决理由成立); 但 F1 有更简形态: 不加新 AC、不动 gate,
AC28 加一个 checkbox + 一条 command 证据即补回失守的 worktree 计数; F2 顺 G1 之刀边际成本一行。
