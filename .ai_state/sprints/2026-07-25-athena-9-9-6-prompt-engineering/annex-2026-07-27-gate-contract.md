---
sprint_slug: "2026-07-25-athena-9-9-6-prompt-engineering"   # 2026-07-28 并入; 原拟 2026-07-27-athena-9-9-6-hotfix-gate-contract
path: "System"                # 2026-07-28 用户拍板并入 System sprint; 原建议值 Feature 作废
created: "2026-07-27"
last_updated: "2026-07-28"
document_status: "superseded-merged-as-annex"
baseline_release: "9.9.6"
target_release: "9.9.6-hotfix"
---

> ⚠️ **本档已并入, 不再是独立 sprint 的 design**。2026-07-28 用户拍板把 A-E 五条作为**追加范围**
> 并进 `2026-07-25-athena-9-9-6-prompt-engineering`, 不另立 sprint。
>
> - **门禁真相在** 同目录 `design.md` §12 (方案摘要) 与 §13 AC19-AC28 (验收标准) —— delivery-gate
>   只读 `design.md`, 本档不参与任何机械校验。
> - **本档保留的价值**: 逐条源码行号锚点、备选方案对比表 (§三)、风险与缓解 (§五)、实施成本表 (§六)、
>   撰写中发现的额外问题 (§七)。§12 是压缩版, 论证细节以本档为准。
> - **原 AC1-AC10 已重编为 AC19-AC28** (映射见 §13 表头注)。本档正文的 AC 编号未改, 引用时按映射换算。
> - **F 条 (batch/debt 路径) 仍待用户拍板**, 未拍板前照 F-a 执行 (见 §二 F 与 AC26 的反向断言)。

# Design · Athena 9.9.6 hotfix — gate 契约可见性与派工时序 (annex, 已并入)

> **证据基地 (一手, 只读)**: 消费侧 `quantum-cowork/.ai_state/sprints/2026-07-27-ledger-debt-batch/`
> (design.md R3.1-R3.5 · critic-r1.md · critic-r2.md · evidence.yaml · route-note.md · token-usage.yaml)。
> 本设计的每条改进都追溯到该 sprint 2026-07-27 当天的具体失败 (ratchet 原则, `~/.claude/rules/iron-law-provenance.md`)。
>
> **判据原则** (引 iron-law-provenance「文档层不可作为一手事实」的引申):
> **门禁的判据必须在它所约束的文档模板里可见, 否则就是隐藏考纲。**
>
> 撰写会话只产出本设计, 未改任何 harness 文件。行号引用以 2026-07-27 安装态
> `~/.claude/hooks/delivery-gate.cjs` (1213 行, 与 Rlues `vibeCoding/claude/9.9.6/.claude/hooks/delivery-gate.cjs` 逐字节一致, `diff` 已验空) 为准; 行号会漂移, 故每处均附函数/常量名作主锚点。

## 一、背景 (WHY)

消费侧 2026-07-27 一次真实 Refactor sprint (ledger-debt-batch, 六项小债批次) 的实测损耗:

- 主 agent 会话约 49 万 token, 7 次 subagent 运行约 78 万 token (用户当日会话复盘口径);
  其中因下述缺陷 **两个 worktree 写者整轮撞墙、约 21 万 token 花在被阻断的运行上**。
  可核旁证: 该 sprint `token-usage.yaml` 主会话计费口径 total_tokens=555,183 / output=388,856 / cache read 5,400 万。
- 同一组基线被 5 个独立主体从零重测 (见 C 条), 复核本身有效但成本形态错了。

八条具体失败与一手出处:

| # | 失败 | 一手档案 |
|---|---|---|
| 1 | AC 段标题 `## 六、验收标准 (AC)` + 表格形态 → gate 解析出 0 条 AC, 三个在飞写者全部被 spec-gate 阻断 | ledger design.md R3.1 (`:272-284`); gate `ACCEPTANCE_HEAD` (cjs:613) + `acceptanceCriteria()` (cjs:626-641) |
| 2 | 主 agent 在写者已开工后才把 `_index.md` 翻到 `stage: impl`, 门禁当场对在飞写者生效 | ledger design.md R3.1 末段 (「根因是主 agent 的」); `~/.claude/settings.json` PreToolUse matcher `Edit\|Write\|MultiEdit` |
| 3 | 业务 AC 占用 harness 保留元标号 (编号 11/12) → 恰是最需要证据的两条 AC 被**静默免检** | ledger design.md R3.4 (`:311-320`); gate `validateAcMapping` 排除行 (cjs:813) + `validateMetaAcceptance` (cjs:852-866) |
| 4 | evidence 绑定字段 (`ac_id`/`covers`) 无任何文档提及: hook 自动采集的 26 条记录命中数 = 0 (2026-07-27 实测 `grep -cE '^\s+(ac_id\|covers)\s*:' evidence.yaml` = 0) | ledger `evidence.yaml`; `evidence-collector.cjs` (只写 tool_use_id/tool/result/command/timestamp); gate `parseEvidenceRecords` (cjs:771-799) |
| 5 | critic 轮次判据是 design.md 里字面串 `Critic` + 空格 + `Findings` 的出现次数; 初版写「Critic 轮次」节 (现档 `:363` 仍存) 计 0, 补字面段头 (`:335`/`:350`) 才被认 | gate `validateCriticRounds` (cjs:599-607, 计数在 :602, Refactor/System 地板 2 在 :605) |
| 6 | 同一组基线 (`sqlite_master` 45 行 / 20 影子表 / 24 真实表 / `loop.ts` 310 行 / `run()` 163 行) 被独立测了 5 次 | ledger route-note.md `:9-20` (主 agent) · critic-r1.md「基线复核」节 · design.md `:235-239` (R2 与两写者复核记录) |
| 7 | critic 的「纯重构测试零修改」可达性检索式抓不到 `(childLoop as unknown as {...}).tools` 类私有字段访问 —— 对 `tsc --noEmit` 与 import 分析双隐形 | ledger design.md R3.2 (`:287-300`, `phase2-5b-stack-spawn.test.ts:170`/`:201`) |
| 8 | 量化 AC 写 `≥1966` 允许「一片删测试另一片加测试」互相抵消 | ledger critic-r1.md F9; design.md AC15 (`:261`, 已改绝对相等 + 构成式) |

## 二、方案

按落点分四层 (对齐 `2026-07-25-harness-gate-p1-p4` 的「分层对症」先例), **本 hotfix 只做模板层 + rules 层 + references 层; hook 层仅列可选项, 待拍板项零实施**:

| 层 | 条目 | 本刀是否实施 |
|---|---|---|
| 模板 (pace templates) | A (契约注记块) · C (已验证基线节) | 是 |
| rules (`~/.claude/rules/` + 双端发行件) | D (检索式检查项) · E (量化 AC 记法) | 是 |
| skill references (`pace/references/stages.md`, `orchestration.md`) | A (ship 绑定义务) · B (派工时序约定) | 是 |
| hook (`delivery-gate.cjs`/`.py`) | A 的错误消息增强 · A5 计数锚定 · B 的 spawn 侧机械化 | **否, 列为可选/下刀, 见 §三** |
| 待拍板 | F (batch/debt 路径) | 否, 仅记录 |

### A · 把 delivery-gate 的机器契约写进它所约束的模板 (最高价值)

**契约事实 (逐条对源码核实, 2026-07-27)**:

1. `ACCEPTANCE_HEAD` (cjs:613 / py:395): 只认 `## Acceptance Criteria` / `## 验收标准` (2-3 级标题),
   序号前缀只允许 ASCII `\d+[.)]` —— CJK 序数 `## 六、验收标准` 不匹配。
2. `acceptanceCriteria()` (cjs:626-641): 节内只收列表项 `^\s*(?:[-*]|\d+[.)]|\[[ xX]\])\s+\S`,
   **markdown 表格行一条都不算**; 占位符/泛化陈述被 `isPlaceholderCriterion` (cjs:619-624) 剔除。
3. `validateCriticRounds` (cjs:599-607): 数的是 design.md 里**字面** `Critic` + 空格 + `Findings`
   的出现次数 (cjs:602), Refactor/System 地板 = 2 (cjs:605)。
4. 编号 11/12 是 **harness 保留元标号**: `validateMetaAcceptance` (cjs:852-866) 命中 11 号要求
   evaluator VERDICT=PASS (cjs:857), 命中 12 号要求 cleanup 证据 + 活动 worktree 数 = 1 (cjs:860-866);
   且 cjs:813 把这两个标号**排除在「每条 AC 必须有 admissible 证据记录」的绑定校验之外**。
   排除本身有正当理由 —— CX 侧 py:666-667 注释自陈: 给元 AC 造 evidence 行是循环论证。
   缺陷不在排除, 在**保留语义任何模板/skill 都没写**, 业务 AC 占用即静默免检。
5. `validateAcMapping` (cjs:807-848) 只认 `evidence.yaml` 记录里的 `record.ac_id` / `record.covers`;
   admissible 记录三形态 (cjs:819-844): `source: command` (要 output_artifact + sha256 + exit 0 +
   implementation_commit 绑 reviewedCommit) / `source: artifact` / `source: review` (指向含
   `## Spec Compliance` + `## Evidence Cross-Check` + 逐 AC SATISFIED 行 + VERDICT PASS 的最新 review)。
   而 hook 自动采集的记录**没有这两个字段** (evidence-collector.cjs 不写); 写者交的
   `tdd-evidence.yaml` 走 `validateTddEvidence` (cjs:495-514) 另一条校验, **不参与 AC 绑定**。
   触发条件: 该校验仅在 `review-manifest.yaml` 存在时执行 (cjs:984-988), 而 Refactor/System
   的 manifest 是强制的 (cjs:970-971) —— 即红区路径**必踩**。消费侧两个 sprint (ledger-debt-batch
   26 条、a1-undistilled-trajectory-guard) 的 evidence.yaml 绑定字段命中均为 0, 说明该契约从未被
   任何写者知晓过。

**修法 (全部文档面, 双端对称)**:

1. **模板注记块**: CC `vibeCoding/claude/9.9.6/.claude/skills/pace/templates/sprints/design.md`
   与 CX `vibeCoding/codex/9.9.6/.codex/skills/pace/templates/sprints/design.md` 的验收标准节
   上方加一个「⚙ 机器契约 (delivery-gate 同步)」引用块, ≤20 行, 五要素:
   标题白名单 + ASCII 序号限制 · 仅列表项计数 (表格不算) · 保留元标号 (编号 11/12) 的语义与
   免检事实 (业务 AC 从 13 起编) · critic 轮次按字面串计数 (段头必须逐字保留) ·
   ACn↔evidence 绑定义务一句话 + 指向 stages.md ship 段。每要素附函数名锚点 (行号为辅)。
   **模板既有骨架 (`## 验收标准 (acceptance criteria)` + `- [ ] AC1:`) 本身是合规的, 不改** ——
   今天的失败发生在消费者**重写**骨架时无任何警示; 修的是可见性, 不是骨架。
2. **stages.md ship 段** (CC/CX 两份 `pace/references/stages.md`): 新增「per-AC 绑定记录」义务:
   review PASS 后、翻 ship 前, 主 agent 为每条业务 ACn 向 `evidence.yaml` 追加一条绑定记录
   (最低成本形态 = `source: review` 指向最新 passN, 前提是 review 档含逐 AC SATISFIED 表);
   附 admissible 三形态速查与「hook 自动采集记录不构成绑定」的显式警示。
3. **evidence 绑定该改模板、改 hook、还是改采集器 —— 权衡与推荐** (详表见 §三):
   推荐**只改模板与 stages.md, hook 与采集器不动**。理由: 绑定必须是**有意为之的断言**
   (谁声称这条命令/审查覆盖了 AC-n, 谁签名), 契约本身是健全的, 缺陷只在不可见;
   采集器自动补 `covers` 等于机器替人签名 = 伪造绑定, 违反铁律[证据与出处];
   放宽 hook (无记录时采信 review 表) 会把三形态中最强的 sha256 锚定形态边缘化。
   可选增量 (P2, 待拍板): hook 的两条 block 消息 (cjs:758 spec-gate 缺 AC 段 / cjs:848 缺绑定)
   补一句「合规骨架与记录样例见 design 模板机器契约块」—— 仅消息串, 行为零变化, 但属 hook 改动,
   影响所有消费方, 须 `harness-patches.md` 登记。

### B · stage 翻转时序规则

**事实**: delivery-gate 挂 PreToolUse `Edit|Write|MultiEdit` + Stop (settings.json 两处注册);
P3 修复后从**主 checkout** 解析 `_index.md` (cjs:1176-1198), 故 worktree 里的写者同样受主仓
stage 支配。且 cjs:1198 对 `stage ∈ {design, impl}` 的实现写入都跑 `validateImplEntry` ——
门禁从翻转那一刻起对所有在飞写者即时生效。今天三个写者开工后 stage 才翻 impl, 全部锁死。

**规则文本 (落 references, 非铁律)**:

> stage 进 impl (含 `current_sprint_slug` 切换) 必须在**首次派工之前**完成;
> 派工前主 agent 必须自检本 sprint design 的 AC 段可被 gate 解析 (见模板机器契约块);
> 存在在飞写者 (`active_worktrees` 非空, 或 subagent-events 有未配对 Start) 时,
> 不得修改 `_index` 的 `stage` / `current_sprint_slug`。

**落点**: `stages.md` impl 工作流新增 step 0 (两端); `orchestration.md`「worktree 规则速查」
追加同义一条。**不进 CLAUDE.md 铁律** —— 9.9.6 设计 §8 明确「stages.md 是 stage 义务真相」,
且 CLAUDE.md 受常驻预算约束 (9.9.6 候选铁律「常驻预算是一等约束」)。

**能否机械化 —— 能, 但不在本刀** (hook 改动, 影响全体消费方, 列下刀候选):

- 方案 B-m1 (推荐): 扩展 `subagent-worktree-check.cjs` (已挂 PreToolUse `Agent`, 天然的派工关口):
  spawn generator 时若 stage ∉ {impl} 或 AC 段解析为 0 条 → block spawn, 报可执行解锁链。
  优点: 在**正确的边界** (派工时刻) 拦, 不碰 `_index` 写入路径。
- 方案 B-m2: delivery-gate 在 `_index.md` 写入时 diff frontmatter, 在飞写者存在则拒改 stage。
  缺点: `_index.md` 有已知 lost-update 与 hook churn 问题 (消费侧 memory 实测两条);
  写者崩溃后永无 Stop → stage 永锁, 必须再设逃生口 —— 复杂度不成比例。

### C · 共享「已验证基线」载体

**事实**: 同一组基线被独立测 5 次 (主 agent 分诊 route-note:9-20 → critic R1「基线复核」→
critic R2 → S1/S2 两写者各自重测)。复核本身是对的 —— 正是复核推翻了 critic R1 建议的
`sql IS NULL` 影子表判据 (实测命中 0 行, critic-r1 F10) 和主 agent 自己的 AC 判据
(未修代码上恒绿, critic-r2 F1)。**设计目标 = 降低复核成本, 不是取消复核。**

**修法**: route-note 模板 (CC/CX 两份 `pace/templates/sprints/route-note.md`) 新增节:

```markdown
## 已验证基线 (verified baseline)
| 事实 | 测量命令 (单条可复跑) | 实测值 | 测于 (commit/时刻) | 已复核方 |
```

派工契约随附该节 (orchestration.md 派工段注明)。写者义务两句, **边界必须写死**:

> 写者对自己依赖的每条基线**必须复跑所附命令核对** (一条命令, 而非从零推导);
> 不一致 → 立即停下上报, 两个值都留档。**不得退化为采信不复核** ——
> 无测量命令的基线条目视同未验证, 不得作为 AC 或裁决依据 (对齐 coding-standards
> 「量化验收标准必先核基线」的出处要求)。

### D · 类型不可见依赖进 review 检查单

**事实**: critic R1 判「纯重构可做到测试零修改」用的检索式是「查 prototype 打桩 + 查直接
import」, 抓不到 `(childLoop as unknown as { tools: ToolRegistry }).tools` 这类私有字段访问
(ledger design R3.2): 它对 `tsc --noEmit` 隐形 (运行时形状改了仍 EXIT=0), 对 import 分析也
隐形; 且同型写法在消费侧成族存在 (`audit.test.ts` 等直读 `storage.db`)。S2 写者的收尾结论
(转引自当日复盘, 档案实质见 ledger design R3.2) 直接作为原则句:

> **可达性论证所用的检索式, 必须能抓住该 AC 自己要防的那类失败。**

**修法**: `coding-standards.md` (USER 级 `~/.claude/rules/` + CC 发行件 `.claude/rules/` +
CX 发行件 `.codex/standards/`) 的 review 相关段新增 P1 检查项: 声称「纯重构 / 测试零修改 /
无外部消费者」前, 检索式至少覆盖类型系统不可见的依赖 ——
`as unknown as` · `as any` · 对私有/内部字段的运行时访问 (含索引访问与 `.db` 式内部读) ·
prototype 打桩 · 动态 require/import。附上面的原则句与 R3.2 出处。

### E · 量化 AC 写绝对值而非 `≥`

**事实**: `≥1966` 在三写者并行时允许「一片删测试、另一片加测试」互相抵消 (critic-r1 F9);
当天 AC15 已改为 `1966 + 各片新增数` 的绝对相等 + 构成式 (ledger design.md:261), 合并后实测
1976 与构成式吻合。

**修法**: `doc-style.md` (USER 级 + CC/CX 发行件, 沿用 2026-07-25「tdd-evidence backfill 记法」
在该档落 gate 相关记法的先例) 新增「量化 AC 记法」: 并行多写者场景的计数类 AC 必须写
**绝对相等 + 构成式** (基线 + 各片增量 = 总量), 禁 `≥`; 单写者可用下界, 但基线值必须附
测量命令与出处 (与 C 的基线节、coding-standards 基线条款互为引用)。

### F · 流程成本: batch/debt 路径 (只提出问题, **待用户拍板**)

**事实**: Refactor 地板 = critic ×2 (cjs:605) + 3 写者 + 2+1 review ≈ 9 次冷启动 subagent,
当天 subagent 侧约 78 万 token。对「六项互不相干的小债」是超配。但 **critic 不可削**:
两轮 18 条 findings 含 3 条 P0, 其中 critic-r2 F1 (验收判据在未修代码上恒绿) 若漏掉,
整片就是假绿 —— critic 是当天回报率最高的环节。

三案 (本刀零实施, 记录供拍板):

| 案 | 内容 | 代价/风险 |
|---|---|---|
| F-a 维持现状 | 批次按最重切片取路径地板 | 成本照旧; ratchet 原则完好 |
| F-b 新增 batch/debt 档 (**撰写者推荐**) | 一次分诊 + 一份 design (critic 地板保持 2) + 各片单写者 + **合并后一次 2+1 review 覆盖全批**; 机械边界: 各片文件面互不相交、单片 ≤10 文件、跨片 AC 必须显式署名 (ledger 已两次踩「跨片 AC 无人负责」) | 省下的是重复冷启动, 不是审查覆盖; 风险 = 路径地板是 ratchet (每条追溯到失败), 开新档等于开豁免面, 必须由机械边界而非自觉守住 |
| F-c 逐片走 Feature 挂同一 roadmap | 无新机制 | 丢掉整批合并视角 —— 当天跨片 AC14b/AC15 恰是合并后才有人负责的 |

推荐 F-b 的理由: 它保住今天被证明有效的两个环节 (critic ×2、合并后全量复跑), 只削去
被证明超配的环节 (每片独立 review 冷启动)。**不替用户决定; 未拍板前一切照 F-a 执行。**

## 三、备选方案对比 (关键决策点)

| 决策点 | 备选 | 为何不选 |
|---|---|---|
| A5 evidence 绑定落点 | **改采集器** (PostToolUse 自动补 `covers`) | 采集器不可能知道一条命令覆盖哪条 AC; 自动补 = 机器替人签名 = 伪造绑定, 违反铁律[证据与出处] |
| 同上 | **改 hook** (无绑定记录时直接采信 review 逐 AC 表) | 单点放宽三形态中最强的 sha256/commit 锚定形态; hook 改动波及全体消费方; 契约本身健全, 缺的只是可见性 |
| 同上 | **改模板 + stages.md** (选定) | 零行为变化, 契约从隐藏考纲变成明示义务; hook 消息增强留作 P2 可选 |
| A 契约行号引用 | 只写行号 | 行号必漂 (本文写作期间 gate 刚加过熔断器 ±200 行); 故函数/常量名为主锚, 行号为辅 |
| B 机械化 | 本刀顺带改 hook | hook 改动影响所有消费方且需逃生口设计; hotfix 的纪律是最小面; 约定先落, B-m1 列下刀 |
| C 载体 | 新建独立 baseline.yaml | route-note 已是分诊证据的既有归宿 (铁律[分诊先行]), 新文件违反铁律[反过度工程]「无第二消费者不抽象」 |
| E 落点 | coding-standards.md | 该档管代码与 AC 的质量判据, doc-style 管**记法**; backfill 记法先例已在 doc-style, 同类同档 |
| F | 本刀直接实施 F-b | 用户点名待拍板; 路径地板是 ratchet, 未经拍板不开豁免面 |

## 四、影响范围

**本刀改 (全部文档面, 每处 CC/CX 双端对称; CX 侧 `.codex/standards/` 对应 CC `.claude/rules/`)**:

| 条 | Rlues 发行件 (源) | 安装态同步 |
|---|---|---|
| A1 | `vibeCoding/{claude,codex}/9.9.6/.{claude,codex}/skills/pace/templates/sprints/design.md` | `~/.claude/skills/pace/templates/sprints/design.md` 等 |
| A2/B | 同上两端 `skills/pace/references/stages.md`; B 另加 `references/orchestration.md` | `~/.claude/skills/pace/references/` 同名 |
| C | 同上两端 `skills/pace/templates/sprints/route-note.md` + `references/orchestration.md` 派工段 | 同上 |
| D | 两端 `rules|standards/coding-standards.md` | `~/.claude/rules/coding-standards.md` (+CX) |
| E | 两端 `rules|standards/doc-style.md` | `~/.claude/rules/doc-style.md` (+CX) |
| F | 仅本 design 记录 | 无 |

**不改**: `delivery-gate.cjs` / `.py` (含错误消息) · evidence-collector · 任何 hook ·
CLAUDE.md/AGENTS.md 铁律 · 消费侧项目任何文件。

**台账义务**: 安装态 (`~/.claude`, `~/.codex`) 非 git 仓, 每处安装态改动须在
`.ai_state/harness-patches.md` 登记复核命令 (9.9.3 白名单修复被 9.9.6 升级静默覆盖的 P1
回归是该台账的设立起因, 本刀的 rules 改动同样暴露在该风险下)。
**顺带发现待处理**: `vibeCoding/claude/9.9.6/hooks/delivery-gate.cjs` (LOCAL-PATCHES 入库
快照, 2026-07-26) 已落后于 `.claude/hooks/` 发行件与安装态 (2026-07-27 熔断器 + manifest
gitignore 修复未同步), 而 LOCAL-PATCHES.md 仍声称「与安装态逐字节一致」—— 实施时刷新快照
与台账行, 或显式登记不刷新理由。

## 五、风险与缓解

| 风险 | 缓解 |
|---|---|
| 模板注记块随 gate 演进过期 → 新的隐藏考纲 (契约写两处必漂) | 注记块以函数/常量名为锚 + 尾行标「同步自 delivery-gate @2026-07-27」; 把「gate 判据变更须同步模板注记」写进注记块自身; 根治 (契约单源生成) 超出 hotfix, 记 proposals |
| 模板/规则膨胀触碰常驻预算 (9.9.6 候选铁律) | 模板与 rules 均非 SessionStart 注入面 (模板按 sprint 拷贝, rules 按 stage 显式 Read/attach); 注记块限 ≤20 行, 规则条目各 ≤10 行 |
| C 节被写者当免检凭据 → 复核退化为采信 | 边界句写死「无命令 = 未验证」「必须复跑」; critic/reviewer 检查单 (D 同批落 coding-standards) 增一条: 基线引用无复跑记录 = CONCERNS |
| B 只落约定, 无机械强制, 会再犯 | 约定给出派工前**单条自检命令**降低违约概率; B-m1 (spawn 关口机械化) 列下刀候选, 起因与判据已在本档留痕 (ratchet) |
| rules 改动在下次版本升级时被覆盖回归 (P1 回归同型) | 全部改动落 Rlues 发行件为主、安装态为辅, 并逐条进 harness-patches.md 复核清单 |
| 本档自身触发字面计数假绿 (设计正文若含 critic 段头字面串, `validateCriticRounds` 会把讨论当轮次) | 本档正文刻意以「`Critic` + 空格 + `Findings`」转写, 不出现该字面串; 真实轮次由实施会话追加后自然计数。此脆弱性本身已作为发现记入 §七 |

## 验收标准

<!-- 本节自举遵守 A 条契约: 标题用 gate 白名单原文 (不加 CJK 序号), 条目全为 checkbox 列表项,
     业务标号避开保留元标号 (编号 11/12), 每条可观测、附核验命令口径。 -->

- [ ] AC1: CC/CX 两份 design 模板的验收标准节上方各有一个 ≤20 行的机器契约注记块, 覆盖五要素 (标题白名单+ASCII 序号 / 仅列表项 / 保留元标号语义与业务 AC 从 13 起编 / critic 字面计数 / evidence 绑定义务), 每要素附 gate 函数或常量名锚点; 核验 = `rg -n "机器契约" <两模板>` 各 ≥1 且人工比对五要素齐全。
- [ ] AC2: 红绿对照实测 — 在 /tmp fixture 项目 (含 `_index.md` stage=impl) 用 `node ~/.claude/hooks/delivery-gate.cjs` 喂 PreToolUse 实现写入 payload: 按改后模板骨架填一条真 AC 的 design.md **不被 block**; 复现消费侧原形态 (`## 六、验收标准` + 表格行) **被 block**; 两次输出留档进本 sprint evidence。
- [ ] AC3: CC/CX 两份 stages.md 的 ship 段含 per-AC 绑定记录义务 (触发条件、admissible 三形态速查、`source: review` 最低成本路径、hook 自动采集记录不构成绑定的警示); 核验 = `rg -n "ac_id|covers" <两份 stages.md>` ≥1 且义务段完整。
- [ ] AC4: CC/CX 两份 stages.md 的 impl 工作流含 step 0 派工时序规则 (翻 stage 先于派工 + 派工前 AC 段自检命令 + 在飞写者存在时禁改 stage/current_sprint_slug), orchestration.md worktree 速查含同义条目; 核验 = `rg -n "派工" <三档>` 命中对应句。
- [ ] AC5: CC/CX 两份 route-note 模板含「已验证基线」五列表格节, orchestration.md 派工段注明随契约下传; 边界句逐字含「不得退化为采信不复核」与「无测量命令的基线条目视同未验证」。
- [ ] AC6: 三份 coding-standards (USER 级 + CC/CX 发行件) 的 review 检查项含类型不可见依赖检索清单 (至少 `as unknown as` / `as any` / 私有字段运行时访问 / prototype 打桩 / 动态导入 五类) 与「检索式必须能抓住该 AC 自己要防的那类失败」原则句及 R3.2 出处引用。
- [ ] AC7: 三份 doc-style (USER 级 + CC/CX 发行件) 含量化 AC 记法 (并行多写者 = 绝对相等 + 构成式、禁 `≥`; 单写者下界须附基线测量命令与出处), 并交叉引用 C 的基线节。
- [ ] AC8: F 条在本档保持「待用户拍板」形态 — 本 sprint 的 git diff 不含任何 batch/debt 路径的 skill/hook/模板实现; 核验 = diff 审读。
- [ ] AC9: 双端对称性 — 每处 CC 改动有 CX 对应落点, 或在本档影响范围表显式登记不对称原因 (CC/CX 只对齐语义, 不伪造对称); 核验 = 对照 §四 表逐行检查。
- [ ] AC10: 安装态与 Rlues 发行件双写一致 (逐文件 `diff` 空), 且 harness-patches.md 为本刀每处安装态改动新增带复核命令的台账行; §四「顺带发现」的 LOCAL-PATCHES 快照漂移已刷新或已登记不刷新理由。

## 六、实施成本一览

| 条 | 成本 | 主要风险 | 建议优先级 |
|---|---|---|---|
| A | 低 (4 个模板/references 文件 + fixture 实测) | 注记块过期漂移 (见 §五) | **1 (最高)** |
| B | 低 (3 个 references 文件) | 无机械强制, 靠自觉 + 自检命令 | **2** |
| C | 低 (2 模板 + orchestration) | 复核退化 (边界句 + 检查单缓解) | 3 |
| D | 低 (3 份 rules) | 检索清单不全 (原则句兜底: 清单是下限不是上限) | 4 |
| E | 低 (3 份 rules) | 无 | 5 |
| F | 零 (仅记录) | 拍板前误实施 (AC8 反向断言看住) | 待拍板 |
| A-hook 消息增强 / B-m1 spawn 机械化 | 中 (双端 hook + fixtures + 台账) | 波及全体消费方项目 | 下刀, 不在本 hotfix |

## 七、撰写中发现的、任务清单之外的问题 (留痕, 不在本刀扩面)

1. **critic 轮次字面计数可被正文讨论污染**: `validateCriticRounds` 全文匹配, 任何**讨论**该契约的
   design (含本档、含 A1 修后的模板注记块) 都可能虚增轮次计数 → 检查被平凡满足。本档以转写规避
   (本节初稿曾原样写出该字面串作正则示例, 自检时抓获 —— 恰是问题的现场演示);
   根治 = 计数锚定到 2-3 级标题行内出现该字面串, 属 hook 改动, 记 proposals 待下刀。
2. **LOCAL-PATCHES 快照漂移** (见 §四): 入库快照落后安装态一天, 台账声明已失真 —— 台账机制
   本身需要「快照新鲜度」的复核命令。
3. **evidence 绑定分级触发的暗差**: `validateAcMapping` 仅在 manifest 存在时执行 (cjs:984),
   非红区 sprint 不带 manifest 时业务 ACn **完全不绑定证据** —— 同一份 AC 在 Feature 与
   Refactor 下的实际强制力差一整级, 模板注记块应写明这一分级 (已并入 A1 五要素的绑定义务句)。
4. **消费侧 A1 sprint 佐证**: 其 evidence.yaml 同样 0 条绑定字段且 sprint 目录无
   review-manifest.yaml —— 绑定契约在该消费方项目从未被真正行使过, ledger-debt-batch 的 ship
   将是第一次实弹; 若 A 条不先落地, 下一次撞墙已经排在路上。
