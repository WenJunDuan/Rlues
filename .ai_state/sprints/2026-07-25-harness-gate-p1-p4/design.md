# Design · harness 门禁修复 P1-P6 (2026-07-25)

> 来源: 用户 2026-07-25 拍板修 proposals P1-P4; 分诊亲验后扩为 6 条 (P5/P6 新发现)。证据见 route-note.md。
> 对象: `~/.claude/hooks/delivery-gate.cjs` (969 行门禁中枢) + `~/.codex/hooks/delivery-gate.py` + 规范/skill 文档 + Rlues 源仓库 + 项目档案。铁律[Hook 是进化器]。
> **路径调整 (2026-07-25, 用户显式批准)**: Refactor → **Feature**。原因: 改动对象全在项目 repo 之外, worktree 对其零隔离效果却**禁止写入** (P4 实测), 而 `subagent-worktree-check.cjs:107` 对红区无条件强制 worktree 且**无任何豁免出口** (亲验 135 行全文, 不读 _index 任何字段) → 这本身是新缺陷 **P9** (已记 proposals, 本 sprint 不修, 因修它要写 hook 而写 hook 又被它拦, 鸡生蛋)。降黄区后 generator 可正常作业; **降级不降质**: critic 2 轮 (17 findings/4 P0)、G1-G5 dry-run、手工备份、Rlues 入库根治全部保留。

## Round 1

### 背景 (WHY)

四条 proposals 已连续三个 sprint 逼出契约豁免或绕行 (批次1 idle 释放 · 批次2/3 skip_impl_subagent_check 豁免 · 批次2/3 cwd 误拦与写隔离绕行)。分诊亲验后暴露两条新问题, 且发现 **P1 是回归** (9.9.3 期用户拍板的白名单修复被 9.9.6 升级覆盖) —— 说明不解决 P5 (无 patch 层), 本次修复同样会在下次升级消失。

根因分三层, 修法必须分层对症:
- **代码层 (P1/P2/P3)**: gate 判据与真实 harness 行为错位 → 改 gate
- **规范层 (P6)**: gate 要求八字段全非空, 与"backfill 测试无独立 red 阶段"的合法工程形态冲突 → **不改 gate, 改档案记法 + 落规范** (克制: 既有机制已能表达)
- **平台层 (P4)**: subagent 写入隔离是 Claude Code 语义, hook 改不了 → 改流程文档 (spawn 决策)
- **存续层 (P5)**: 本地 patch 无台账无版本 → 建 patch 台账 (不做自动化)

### 方案

**W1 (P1) 白名单补齐 hook 持续维护文件** — `delivery-gate.cjs:404-411` `allowedExact` 集合补三项:
`${sprintRel}/token-usage.yaml` (token-usage-collector.cjs:397 实际写此名, 每次 Stop 先于 gate 改写) · `${sprintRel}/stop-failures.jsonl` (stop-failure-recorder.cjs 于 block 事件追加) · `.ai_state/proposals.md` (铁律[Hook 是进化器]指定的 Stop 反思落点)。三者均为**过程记账**, 非被审对象。保留既有 `token-usage.jsonl` 条目 (向后兼容, 不删)。注释注明"9.9.3 期已修, 9.9.6 升级回归, 2026-07-25 重修 + P5 台账登记"。

**W2 (P2) generator 生命周期放宽为"收束"语义** — `:170-189` 循环内:
- `starts.length !== 1` → `starts.length < 1` (msg: `requires at least one SubagentStart`)
- `stops.length !== 1` → `stops.length < 1` (msg: `requires at least one SubagentStop`)
- **新增**: 按 `parsedTimestamp` 排序后末次事件必须是 `SubagentStop` (否则 `must end with SubagentStop (work not settled)`) — 这是"恰一次"真正想守的东西: 作业已收束, 而非物理只跑一次
- 时序比较基准改为 **首个 Start** 与 **末个 Stop**: `firstStart = starts[0]` (已按读入序, 需显式按时间戳取 min)、`lastStop` (按时间戳取 max); 三条既有断言 (assignment ≥ firstStart · lastStop ≥ firstStart · lastStop ≥ assignment) 语义不变
- `agent_type` 一致性: 由"首 Start 与首 Stop 相等"改为"该 agent_id 全部事件的 agent_type 唯一" (更强, 且续跑不破)
- **不放宽的**: 仍要求有 role=generator 的 assignment 握手 (:153) 与 assignment 不早于首 Start — 防"无握手就声称有 generator"

**W3 (P3) 项目根解析归一到主仓** — 新增 helper (放在 `gitText` 之后):
```js
// P3 fix: worktree 内 --show-toplevel 返回 worktree 路径, 导致 gate 以 worktree 为根解析
// .ai_state (gitignored 档案在新检出必然缺失 → 误拦)。--git-common-dir 在 worktree 内返回
// 主仓 .git; --path-format=absolute 保证主仓内也是绝对路径 (裸 --git-common-dir 在主仓返回 ".git")。
// 实测见 route-note (git 2.54.0); 需 git ≥2.31。
function repoRoot(cwd) {
  const gitDir = gitText(cwd, ["rev-parse", "--path-format=absolute", "--git-common-dir"], "repository root").trim();
  if (!gitDir) throw new GateError("cannot determine Git repository root");
  return path.dirname(gitDir);
}
```
`:386` 与 `:789` 两处 `gitText(cwd, ["rev-parse","--show-toplevel"], ...)` 全部替换为 `repoRoot(cwd)`。**注意 :790** `worktree list` 仍以 root 为 cwd 执行 — 归一后语义更正确 (主仓视角数 worktree)。

**W4 (P6) backfill 形态用既有机制显式表达 (零 gate 改动)** — 判据: gate 只查字段**非空** (`!value`), 不查内容。故 backfill 记录写:
`red_command: "N/A — backfill 测试 (既有实现已正确), 无独立 red 阶段; 缺口证据见 red_summary"`
即合规且诚实。**否决"放宽 gate 允许 red_command 为空"**: 门禁存在的意义就是防"没做 TDD 却声称做了", 放宽会开真口子; 而 backfill 是合法形态, 用显式声明表达即可。落两处:
1. 修批次 3 `tdd-evidence.yaml` 6 条缺 `red_command` 的记录 (provider-utils / run-utils / skill-embeddings / foreach / step-executors / distill-step) — 补显式 N/A 行, 不改任何既有 summary/时间戳
2. 规范落盘: `~/.claude/rules/doc-style.md` 或 pace references 增一段"tdd-evidence backfill 记法" (generator 择 doc-style 更合适处, ≤10 行)

**W5 (P4) spawn 决策文档化** — 平台限制不可修, 改的是**编排知识**: 在 `~/.claude/skills/pace/references/stages.md` 的 polish stage 段 (generator 先 rg 定位) 增注:
> polish_worker 是串行唯一写者, **不加 `isolation: worktree`** — 带隔离会使其无法写主仓 `.ai_state` 与 architecture/ (平台 isolation 语义), 只能靠分支合并或 cp 传递, 多一跳且易漏。同理: 改动对象在项目 repo 之外 (如 `~/.claude` harness) 时不用 worktree, 隔离手段改为手工备份 + 单写者串行。

**W6 (P5) harness patch 台账** — 新建 `.ai_state/harness-patches.md` (项目内, 随项目 git 版本化): 逐条记录"对 `~/.claude` 的本地修改 + 一句话理由 + **可执行复核命令**", 升级 harness 后逐条跑复核即知是否被覆盖。**不做自动化 patch 工具** (无第二消费者, 手工复核 4 条成本 < 造工具)。同时实施前把 gate 备份到 `~/.claude/backups/delivery-gate.cjs.pre-p1p6-<UTC-ts>`。

**W7 (用户 2026-07-25 追加: "1 次 REWORK 的问题也一并修") 量化 AC 必先核基线** — 批次 3 REWORK 的根因: design 写下 "所有改动文件 ≤300 行" 时未核 `storage/workflows.ts` 基线已 341 行, 门槛在落笔时即不可达。这是**规范缺失**而非个人失误, 固化为规则: 在 `~/.claude/rules/coding-standards.md` (或 doc-style, generator 择一) 增一段:
> **量化验收标准必须先核基线**: AC 含数值门槛 (行数/覆盖率/耗时/条数) 时, design 阶段必须先测量被改对象当前值并写进 AC 或风险节; 基线已越线的文件要么纳入本批修复, 要么显式记豁免 (附理由与上界), 禁止写下落笔即不可达的门槛。
同时本 sprint 自身遵守此规则 (AC 数值均来自 route-note 亲验)。

### 验证方案 (dry-run, 强制)

`echo '<payload>' | node ~/.claude/hooks/delivery-gate.cjs` — 放行则**无输出**, 拦截则 stdout 出 `{"decision":"block",...}`。三组必测 (fixture = 项目真实档案, 临时切 `_index` 字段的副本或临时 sprint 目录, **不污染主档**):

| 组 | 场景 | 期望 |
|---|---|---|
| **G1 放行面** | 批次3 sprint (stage=ship) + token-usage.yaml/stop-failures.jsonl working drift + 6 条 backfill 记录补 N/A 后 | **放行** (无输出) — 同时证 W1+W4 生效 |
| **G2 拦截面 (防修成筛子)** | 逐一注入: manifest 哈希篡改 · 删 cleanup-pass.md · 最新 passN VERDICT 改非 PASS · checklist 留一条 pending | **每一项都仍 block** 且 reason 对应 |
| **G3 P2 边界** | ① 多 Start/Stop 且末次为 Stop (批次3 真实 events) → 放行; ② 只有 Start 无 Stop → block; ③ 末次事件为 Start (Stop 在中间) → block; ④ 无 role=generator assignment → block | 4 项各如列 |

G3 需临时构造 events fixture (放 sprint 副本目录, 跑完删)。**gate 语法**: 每次改动后 `node --check ~/.claude/hooks/delivery-gate.cjs`。

### impl 切片 (单写者串行, 每片 dry-run 后 commit)

1. **备份 + W1 + W3** (低风险: 白名单 + helper 替换) → `node --check` + G1 部分 + G2 全组
2. **W2** (逻辑放宽) → G3 全 4 项 + G2 复跑
3. **W4** (批次3 档案补 N/A + 规范落盘) → G1 完整放行
4. **W5 + W6** (stages.md 注记 + harness-patches.md 台账) → 全组回归复跑

### 影响范围

- 改 (repo 外, 需 patch 台账): `~/.claude/hooks/delivery-gate.cjs` (W1 +3 行 / W2 ~15 行 / W3 +8 行 helper + 2 处替换) · `~/.claude/skills/pace/references/stages.md` (W5 ≤6 行) · `~/.claude/rules/doc-style.md` (W4 规范 ≤10 行)
- 改 (项目内): `.ai_state/sprints/2026-07-24-src-health-batch3/tdd-evidence.yaml` (W4, 6 条各 +1 行; **注意会使批次3 review-manifest 的 tdd-evidence 哈希失效** → 同步刷新 manifest + pass2 binding manifest sha, 与批次3 ship 时同法) · `.ai_state/proposals.md` (P1-P6 勾销/更新)
- 新: `.ai_state/harness-patches.md` · `~/.claude/backups/delivery-gate.cjs.pre-p1p6-<ts>`
- 不动: gate 其余 ~940 行判据 (fail-closed 骨架/manifest/binding/spec-gate/light-ship) · 其他 17 个 hook · 项目 `src/`

### 风险与缓解

- **改坏门禁 = 所有项目所有 sprint 被 block** (最高风险): 备份先行 + `node --check` 每片 + G2 拦截面全组回归 (证明没修成筛子) + 改动限于 3 处局部, 不触 fail-closed 骨架
- **W2 放宽被滥用** (真跑了一半就声称完成): 由"末次必须 Stop"+ assignment 握手双守; G3-②③ 专测此面
- **W4 被读成"允许编造 red"**: N/A 文本必须含理由且 red_summary 须有真实缺口证据; 规范文档明写"仅限既有实现已正确的 backfill, 修 bug 类改动仍须真 red"
- **批次3 manifest 哈希连锁**: W4 改 tdd-evidence → manifest/binding 同步刷新 (批次3 ship 已有先例流程)
- **无 git 回滚** (`~/.claude` 非 repo): 备份是唯一回滚路径, AC 强制其存在且可 `diff` 比对
- 基线: 项目 1811 pass / tsc 0 (本 sprint 不动 src, 仅收尾复跑一次确认无副作用)

#### (作废 — 见 Round 3 权威节) Round 1 的 AC 草案

1. `rg -c 'token-usage\.yaml|stop-failures\.jsonl' ~/.claude/hooks/delivery-gate.cjs` ≥2 且 `rg -c '"\.ai_state/proposals\.md"' ~/.claude/hooks/delivery-gate.cjs` =1
2. `rg -c 'show-toplevel' ~/.claude/hooks/delivery-gate.cjs` = **0**; `rg -c 'path-format=absolute' ...` =1; `repoRoot(` 调用点 =2
3. `rg -c 'starts\.length !== 1|stops\.length !== 1' ...` = **0**; 新逻辑含"末次事件为 Stop"判定 (rg 命中错误消息串)
4. **G1 放行 / G2 四项全 block / G3 四项各如期** — 每项贴实际 stdout 摘要入 tdd-evidence
5. `node --check ~/.claude/hooks/delivery-gate.cjs` exit 0
6. 备份存在: `ls ~/.claude/backups/delivery-gate.cjs.pre-p1p6-*` 命中 ≥1, 且与改后文件 `diff` 非空 (证明确实改了且能回滚)
7. `.ai_state/harness-patches.md` 存在, 列全 4 项 repo 外改动 (gate×3 + stages.md + doc-style.md), 每条带可执行复核命令
8. 批次3 `tdd-evidence.yaml` 6 条 backfill 记录均有非空 `red_command` 且含"N/A"与理由; 批次3 review-manifest 的 tdd-evidence 哈希与 pass2 binding manifest sha 同步刷新一致
9. `.ai_state/proposals.md` P1-P4 标注处置结果 (修复/重定界), P5/P6 补录并标注处置
10. 项目 `bun test` 1811 pass + tsc 0 不变 (无副作用)
11. (W7) coding-standards.md 或 doc-style.md 含"量化 AC 必先核基线"段; harness-patches.md 登记该文件改动与复核命令

## Round 1 · Critic Findings (VERDICT: NEEDS_REVISION, 2026-07-25, opus fallback)

10 findings, 2 个 P0。主 agent 已 trust-but-verify 亲验其中四条决定性事实, **全部证实**:

- **F1 [P0]** W2 在自己的举证数据上仍 block: batch1 role=generator `ac31263f6412` = **8 Start / 0 Stop / 末次=Start** (亲验); 新判据"≥1 Stop + 末次须 Stop"照样拦。且与 `compound/2026-07-22-decision-e3-4-generator-truncation-subagent-check.md` 已拍板结论 ("缺 Stop = 真没收尾, 走 flag 释放") 正面冲突
- **F2 [P0]** W3 改错病灶: P3 真实病灶是 `:943 findAiState(cwd)` 而非 :386/:789 的 root; 只换 root 会造成 root=主仓 + aiState=worktree 错配 → `sprintRel` 变 `../wt-x/...` → **任何 .ai_state drift 都 block**, 且 worktree 侧 drift 反而 fail-open
- **F3 [P1]** `dirname(--git-common-dir)` 在 submodule (`.../.git/modules/<n>` → `.../modules`) 与 bare (`/x/repo.git` → `/x`) 下推出非仓库根 → 那类项目**永久 block**; 且 AC2 的 `show-toplevel = 0` 禁掉了唯一安全兜底
- **F4 [P1]** 本 sprint 自己会走 **light-ship** (亲验: 非 .ai_state 改动 = README 40 行 ≤ `SHIP_LIGHT_MAX_LINES=60`) → validateShip 提前 return, manifest/tdd/binding/critic 轮数/generator-chain 全跳过; `isLightShipFile` 的 `hooks/` 护栏只看仓内路径, `~/.claude` 改动天然不可见 → **门禁改动零机械复核**
- **F5 [P1]** dry-run fixture 写法不可执行: 放仓内 → 未跟踪文件落进 `implementationDrift` 被拦; 放 /tmp → 非 git, `gitText` 抛错。正解 `git clone --local --no-hardlinks`
- **F6 [P1]** G2/G3 漏本次改动自身回归面; **batch3 无 `subagent-assignments.jsonl`** (亲验) → G3-① 期望不成立
- **F7 [P1]** `.ai_state/proposals.md` 进白名单是**实质放宽**: 无任何 hook 写它 (只有 gate 注释提到), 它是 agent 手写档 → 不该进
- **F8 [P2]** W4 回改批次3 已 ship 档案无机械收益 (validateShip 只读 `current_sprint_slug`, 指针一移即不再被读)
- **F9 [P2]** AC 三处漏洞: **AC8 含字面 "N/A" 会被 `isPlaceholderCriterion` 静默丢弃** (亲验 `PLACEHOLDER_PHRASES` 含 `"n/a"` 且用 `includes`) · AC1/AC2 用 `rg -c` 数行而 :409 一行两条目 · AC10 的 1811 与 route-note 的 "10 Start/8 Stop" 均无测量出处 (后者实测应为全 agent 合计 20/11, generator 单 agent 8/0)
- **F10 [P2]** 改动落点旁注释含失真前提 (gate :156-159 称 "agent_type 恒为 default" 实测非真; ".ai_state gitignored" 实为已跟踪 312 文件); ":790 归一后语义更正确" 论据不成立 (`worktree list` 输出与 cwd 无关)

## Round 2 (重做, 消化 F1-F10 + 两项主 agent 新发现)

### 新发现 A: Rlues 是 harness 源仓库, 但 9.9.x 只存文档 —— P5 有了根治路径

亲验 `/Users/mi_manchi/workspace/Rlues` (用户 2026-07-25 提供): git 管理 (HEAD e5f55b5, 与 origin 同步), `vibeCoding/{claude,codex}/<version>/` 按版本存档。**但 9.3+ 起只存文档** (`claude/9.9.6/` = 5 个 md: RELEASE/CHANGELOG/AI-MIGRATION-GUIDE/REVIEW×3, **无 hooks/**), 8.9 是最后一个存完整代码的版本。且 `rg -l 'token-usage.yaml' --glob '*.cjs'` 全仓 **0 命中** → **P1 修复从未进过 git, 这是"升级即蒸发"的铁证**。
另有现成测试资产: `vibeCoding/scripts/{test-delivery-gate.py, validate-athena-9.9.6.py, test-token-usage-collector.py}` (80 行的 gate 回归脚本) → 验证方案应先复用而非从零造。

### 新发现 B: codex 侧同样有 P1 与 P3, 但没有 P2

亲验 `~/.codex/hooks/delivery-gate.py` (63KB, Python 版): **P1 同型** (collector `:422` 写 `token-usage.yaml`, gate 白名单 `:958` 只有 `token-usage.jsonl`) · **P3 同型** (`:928` 与 `:1089` 均 `rev-parse --show-toplevel`) · **P2 不存在** (无 exactly-one Start/Stop 判定)。→ 用户问的"codex hooks 要不要修": **要, 修 P1+P3 两条**。

### 修订后的修法

- **W1 (P1) 缩为两项 + 两端对称**: 白名单只加 `${sprintRel}/token-usage.yaml` 与 `${sprintRel}/stop-failures.jsonl` (二者确由 collector:397 / recorder:44 写); **删去 `.ai_state/proposals.md`** (F7: 无 hook 写它, 加了是实质放宽; 它的改动落在 reviewed commit 内即无 drift)。codex 侧 `delivery-gate.py:958` 同样补两项。
- **W2 (P2) 缩范围为"resume 收尾放行, 截断仍拦"** (F1): 只改 `starts.length !== 1` → `starts.length < 1`; **保留 Stop 必须存在**, 并新增"末次事件须为 Stop"。依据亲验: batch1 `a248c4aee453`/`a5a5bdc3bb04` = 2 Start/1 Stop/末次 Stop = **合法 resume, 现被拦, 本 W 修**; `ac31263f6412` = 8/0/末次 Start = **真截断未收尾, 修后仍拦 —— 这是正确行为**, 不推翻 2026-07-22 决策 (该场景继续走 `skip_impl_subagent_check` 显式释放)。时序基准: `firstStart` = 按 `parsedTimestamp` 最小者、`lastStop` = 最大者; **同秒 tie 用文件追加序** (稳定排序: 先按时间戳再按行号)。`agent_type` 一致性改为"该 agent_id 全部事件 agent_type 唯一"。**另立 P8** (截断致 Stop 事件缺失) 指向 `subagent-tracker.cjs` / 平台, 本 sprint 不修, 记 proposals。
- **W3 (P3) 重做为 root/aiState 同源 + 安全兜底** (F2/F3): `main()` 改 `const root = repoRoot(cwd); const aiState = findAiState(root) || findAiState(cwd);` (二者同源, 消除 sprintRel 错配); `repoRoot` 加兜底 —— `const gitDir = <--path-format=absolute --git-common-dir>; if (path.basename(gitDir) !== ".git") return <--show-toplevel>; return path.dirname(gitDir);` (submodule/bare 回退, 不永久 block 那类项目); 非 git 目录时 `gitText` 抛 GateError → main 的 `findAiState` 已先返回 undefined 静默 no-op, 保持现状。:386/:789 换 `repoRoot(cwd)`。**删去 ":790 语义更正确"论据** (F10, 不成立)。codex 侧 `:928/:1089` 同法。
- **W4 (P6) 瘦身: 规范先落, 回填可选** (F8): 必做 = 规范段 (backfill 下 `red_command` 写显式声明 + `red_summary` 须含真实缺口证据 + `red_observed_at` 语义为"缺口核实时刻"); **批次3 档案回填降为可选**, 若做则同步刷 manifest 哈希与 pass2 binding 并在 session-log 记一行原因。**规范措辞禁用字面 "N/A"** (F9: 会被 `isPlaceholderCriterion` 的 `includes("n/a")` 丢弃), 改用"backfill 声明"式表述。
- **W5 (P4) 不变**: stages.md polish 段注明 polish_worker 不加 isolation + "对象在 repo 外时不用 worktree"。
- **W6 (P5) 升级为根治** (新发现 A): ① 在 Rlues 建 `vibeCoding/claude/9.9.6/hooks/` 与 `vibeCoding/codex/9.9.6/hooks/`, 把**本 sprint 改动的文件**存入并 git commit (克制: 只入被改文件, 不做全量镜像 — 全量镜像是第二个决策, 需用户拍板); ② 项目内 `.ai_state/harness-patches.md` 台账保留, 每条记 文件/理由/**可执行复核命令**/Rlues 内对应路径; ③ 改前备份到 `~/.claude/backups/`。升级后复核路径: 跑台账命令 → 若被覆盖, 从 Rlues 对应版本目录 diff 恢复。
- **W7 (量化 AC 必核基线) 不变**, 但本 design 自身补齐: 所有 AC 数字附测量命令 (F9)。
- **W8 (新增, F4 建议) 堵 light-ship 洞并给台账机械消费者**: `isLightShipFile` 加一行 `if (/(^|\/)harness-patches\.md$/.test(file)) return false;` → 改 harness 的 sprint 必走全契约; 同时台账从"写死文档"变成有机械消费者的机制 (呼应 compound/README "长文档无人回读"教训)。
- **W9 (新增, 新发现 B) codex 侧对称修 P1+P3** (见上), P2 无需动。

### 验证方案 (重写, F5/F6)

**fixture 构造**: `git clone --local --no-hardlinks <主仓> /tmp/gate-fx-<ts>` (root/.ai_state/commit 自洽, 可随意篡改, 不污染主档); 另 `git worktree add` 一个专测 F2 的 root/aiState 同源; 收尾断言主仓 `git status --porcelain .ai_state` 为空。**先跑 Rlues 现成 `scripts/test-delivery-gate.py` 建立回归基线**, 再补下列组:

| 组 | 用例 | 期望 |
|---|---|---|
| G1 放行面 | clone fixture: stage=ship + token-usage.yaml/stop-failures.jsonl working drift | 放行 |
| G2 拦截面 (防筛子) | ① manifest 哈希篡改 ② 删 cleanup-pass ③ passN VERDICT 非 PASS ④ checklist 留 pending ⑤ **W1 反向: 改 `.ai_state/handoff.md` (不在白名单)** | 5 项全 block |
| G3 P2 边界 (按亲验数据重推) | ① 2 Start/1 Stop/末次 Stop (batch1 a248c4aee453 形态) → **放行** ② 8 Start/0 Stop/末次 Start (ac31263f6412 形态) → **block** ③ 末次为 Start 但中间有 Stop → block ④ 无 role=generator assignment → block | 4 项各如列 |
| G4 W3 正向面 (新增) | ① 主仓根 ② 主仓子目录 cwd ③ 真 linked worktree (root/aiState 同源, 不误拦) ④ 非 git 目录 (静默 no-op 不崩) | 4 项均不误拦/不崩 |
| G5 W8 | 造 harness-patches.md 改动 + 小 diff → 应**不再** light-ship (走全契约) | 走全契约 |

每组贴实际 stdout 摘要入 tdd-evidence。每次改动后 `node --check` (cjs) / `python3 -m py_compile` (codex py)。

### 验收标准 (Round 3 · 权威, 取代 Round 1 草案)

1. **W1**: `rg -o 'token-usage\.yaml|stop-failures\.jsonl' ~/.claude/hooks/delivery-gate.cjs | wc -l` = 2; `rg -c 'proposals\.md"' ...` 白名单区无新增; codex `delivery-gate.py` 同样 2 命中
2. **W2**: `rg -c 'starts\.length !== 1' ...` = 0 且 `stops\.length < 1` 与"末次须 Stop"错误串各 1 命中; 稳定排序注释在位
3. **W3**: `main()` 内 `findAiState(root)` 在位; `repoRoot` 含 basename 兜底分支; :386/:789 无 `show-toplevel` 直呼 (兜底分支内的那一处除外 —— 行为化断言由 G4 覆盖)
4. **G1-G5 全组按上表通过**, 实际 stdout 入 tdd-evidence
5. `node --check` exit 0 + codex `python3 -m py_compile` exit 0
6. 备份存在且与改后文件 diff 非空
7. `.ai_state/harness-patches.md` 列全本 sprint 全部 repo 外改动 (claude gate / codex gate / stages.md / coding-standards.md), 每条含可执行复核命令 + Rlues 对应路径
8. **W4 规范段落盘**, 措辞不含字面 "n/a" (避开 `isPlaceholderCriterion`); backfill 三字段语义写明
9. **W6 根治**: Rlues `vibeCoding/{claude,codex}/9.9.6/hooks/` 内存在被改文件且已 git commit; `diff` 与安装态一致
10. **W8**: `isLightShipFile` 含 harness-patches 分支; G5 证明生效
11. proposals.md: P1-P7 标注处置 + 新增 P8 (截断致 Stop 缺失, 指向 subagent-tracker/平台)
12. 项目 `bun test` = 1811 pass (测量命令 `bun test 2>&1 | tail -4`, 基线来源: 2026-07-25 本会话实测) + `bunx tsc --noEmit` exit 0

### 轮次收口指针 (Round 2 为最终权威)

**W1 (两项, 无 proposals) / W2 (缩范围 + 稳定排序 + 另立 P8) / W3 (root+aiState 同源 + basename 兜底) / W4 (规范先落, 回填可选, 禁字面 n/a) / W6 (Rlues 入库根治) / W8 / W9 / 验证方案 G1-G5 / AC 1-12 全部以 Round 2 为准**; Round 1 的对应条目与 AC 作废。W5/W7 沿用 Round 1。

## Round 2 · Critic Findings (VERDICT: NEEDS_REVISION, 2026-07-25)

critic 判"三处一行级机械缺陷落盘后即收敛, **不需要第 3 轮**"(与用户 2 轮设定一致)。主 agent 亲验两条 P0 决定性事实, **均证实**:

- **F11 [P0]** 机器识别的 AC 集合仍是作废的 Round 1: `ACCEPTANCE_HEAD` (:539) 要求标题含 `验收标准|acceptance criteria`, Round 2 标题写作 `### AC (...)` **不匹配** → spec-gate 绑的是已作废清单 (含已降级为可选的"批次3 manifest 刷新") → 自造死结
- **F12 [P0]** W3 的 main() 改法把 git 抛点放在 `try` 之外 (:942-944 早于 :945 `try {`) → 非 git 目录/git 不可用时 **hook 崩栈**; 且每次 PreToolUse 多跑一次 `git rev-parse`, 废掉"无 .ai_state 静默快退"
- **F13 [P1]** W2 举证**第二次算错**: 亲验 batch1 assignments — `a248c4aee453`=**evaluator**、`a5a5bdc3bb04`=**spec-compliance**, 二者被 :171 `role !== "generator" continue` 跳过, 今天就不受拦, 不能当收益证据。**正确证据**: batch3 `ac0c19601d65a07ea` = **4 Start / 2 Stop / 末次=Stop** (亲验)
- **F14 [P1]** Rlues `scripts/test-delivery-gate.py:14-15` 硬编码指向 **9.9.0 老副本**, 跑绿与被改的这份 gate 无关
- **F15 [P1]** W9 在 codex 侧重复了 F2 的错: 只换 root 未动病灶 `:1259 find_ai_state(cwd)`; 且 W8 未对称 (codex `:1017 SHIP_LIGHT_MAX_LINES` / `:1020 is_light_ship_file` 同样有 light-ship 洞); codex 已有 `git_root()` helper (:1086) 改一处即覆盖
- **F16 [P2]** AC 自身两处陷阱: AC8 正文含字面 `"N/A"` → 被 `isPlaceholderCriterion` 丢弃 (**禁 N/A 的那条 AC 自己先消失**); AC1 的 `rg -o | wc -l = 2` 会被注释里的同名串顶到 3
- **F17 [P2]** 可省两处替换: 在 main 边界把 root 传下去 (`validateShip(aiState, fm, root)`), :386/:789 收到 root 后 `--show-toplevel` 返回 root 本身 (幂等) → diff 更小、submodule/bare 行为零变更, 且避免"drift 用主仓框 / light-ship 与 architecture 计数仍用 worktree 框"的混框

## Round 3 (机械收敛, 消化 F11-F17 — 无需再审)

- **F11 消化 (已落盘)**: Round 1 的 AC 标题降为 `#### (作废 — 见 Round 3 权威节) Round 1 的 AC 草案` (4 个 `#` 不被 `^#{2,3}` 命中), Round 2 的 AC 段标题改为 `### 验收标准 (Round 3 · 权威, 取代 Round 1 草案)` → 机器只会绑权威节。**本节下方的"AC 修订"是该节的最终内容**。
- **F12 消化**: W3 的 `main()` 最终写法 —— 保持 `:942-944` 的 `const cwd = ...; const aiStateLocal = findAiState(cwd); if (!aiStateLocal) return;` **原样在 try 之前**(不动早退与快退语义); 进 `try` 之后再解析: `const root = tryRepoRoot(cwd); const aiState = (root && findAiState(root)) || aiStateLocal;`。新增 `tryRepoRoot(cwd)` = `repoRoot` 的 **不抛版本**(内部 try/catch, 失败返回 `null`), 非 git / git 不可用时退化为 cwd 语义 (与今日行为一致)。`repoRoot` 保留抛错版供 :386/:789 之外的显式调用(若无调用者则不引入, 只留 `tryRepoRoot`)。**G4-④ 必须用 `hook_event_name: "PreToolUse"` 的 payload 也跑一遍** (P3 原始症状就是对 /tmp 的 Write 触发)。
- **F13 消化**: W2 与 G3-① 的举证 agent 换为 **batch3 `ac0c19601d65a07ea` (4/2/末次 Stop)**; 并注明 batch3 **无 `subagent-assignments.jsonl`** → G3 fixture 必须补一条 `role=generator` 握手行 (时间戳早于末 Stop、晚于首 Start), 否则会以 `missing subagent assignments` **假 block** 而非测到 W2 判据。batch1 `ac31263f6412` (8/0/末次 Start) 继续作为 G3-② 的"截断仍拦"证据。
- **F14 消化**: 不把 Rlues 现成脚本的绿当基线。做法: 跑它时用 env/argv 覆盖两处硬编码常量指向**安装态** gate (2 行改动, 属 Rlues 仓内改动, 一并登记 harness-patches); 若覆盖不成立则**删除"先建回归基线"的说法**, 完全以 G1-G5 为准 (避免"文档层/老副本当一手事实"同型错)。
- **F15 消化**: W9 codex 侧与 CC 端**三件事严格对称**: ① 白名单两项 (`:958` 区) ② `:1259 find_ai_state(cwd)` 与 root 同源 + `git_root()` (:1086) 内加 basename 兜底 ③ `is_light_ship_file` (:1020) 加 harness-patches 分支。AC1/AC10 各加 codex 侧断言, 且 codex 侧改动同样 `python3 -m py_compile` 验语法 + 至少跑一次 codex payload 的 dry-run (若 codex gate 可独立执行; 不可则记为已知验证缺口并在 harness-patches 标注)。
- **F16 消化**: AC 措辞禁用会被占位符检测命中的缩写 (`n/a` 等), 改为"**backfill 显式声明**"式表述; 计数类 AC 限定行域 (`sed -n '<起>,<止>p' | rg -o ... | wc -l`) 或断言带引号精确串, 避免注释顶数。
- **F17 消化 (采纳)**: 改为 **`validateShip(aiState, fm, root)` 单点传递** (:962), **不再替换 :386/:789** —— 它们收到 root 作 cwd 后 `--show-toplevel` 幂等返回 root; 同时消除混框风险 (light-ship/architecture 计数与 drift 同框)。W3 的代码改动缩为: 新增 `tryRepoRoot` + main 内两行 + `validateShip` 调用参数一处。

### 验收标准修订 (在 Round 2 的 12 条基础上替换以下项; 其余 9 条不变)

- **AC1 (替换)**: 限定行域计数 —— CC: `sed -n '404,412p' ~/.claude/hooks/delivery-gate.cjs | rg -o '\$\{sprintRel\}/(token-usage\.yaml|stop-failures\.jsonl)' | wc -l` = 2, 且该行域内无 `proposals`; codex: 对 `delivery-gate.py` 白名单行域同法 = 2
- **AC3 (替换, 行为化)**: 不再断言 `show-toplevel` 命中数; 改为 ① `tryRepoRoot` 定义存在且含 try/catch 与 `basename(gitDir) !== ".git"` 兜底分支 ② `validateShip(aiState, fm, root)` 调用点在位 ③ **G4 四情形全过** (含 PreToolUse payload 的非 git 用例不崩)
- **AC8 (替换, 去占位符字面)**: 规范段落盘, 内容包含 backfill 三字段语义 (显式声明式 `red_command` / `red_summary` 须含真实缺口证据 / `red_observed_at` = 缺口核实时刻), 且**规范正文与本 design 的 AC 均不写入会被占位符检测命中的缩写**
- **AC10 (扩充)**: W8 分支在 CC 与 **codex 两端**均在位; G5 在两端各证一次 (codex 若不可独立执行则记缺口)
- **AC13 (新增)**: G3 fixture 含补写的 `role=generator` 握手行, 且 G3-① 放行是因 W2 判据而非绕过 (reason 无 `missing subagent assignments`)

### 轮次收口指针 (Round 3 为最终权威)

**W2 举证与 G3 fixture / W3 的 main 写法与 tryRepoRoot / W9 codex 三件事 / Rlues 脚本基线处置 / AC1·AC3·AC8·AC10 替换 + AC13 新增 / AC 段标题 —— 全部以 Round 3 为准**; 其余以 Round 2 收口指针 → Round 1 原文链为准。**F11 的标题修正已直接落在文中**(不是待办)。
