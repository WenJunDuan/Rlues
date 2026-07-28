# Athena Harness 进化提案 (铁律[Hook 是进化器])

> 📍 **归属说明 (用户 2026-07-25 指示)**: harness (hooks/rules/skills) 的**改动记录与补丁台账归 harness 自己的项目** —
> `/Users/mi_manchi/workspace/Rlues/.ai_state/harness-patches.md` (8 条补丁, 含逐条可执行复核命令; 源码入库 `vibeCoding/{claude,codex}/9.9.6/`)。
> **本文件只保留"在本项目实测发现"的提案记录**(发现过程是本项目的一手事实), 今后 harness 的修复 sprint 一律在 Rlues 立。

> **2026-07-25 状态**: 用户拍板修 P1-P4。分诊亲验后扩为 **P1-P7** — sprint `2026-07-25-harness-gate-p1-p4` design 已落盘 (7 条修法 + 三组 dry-run 验证方案), 处置见各条尾部与该 design。
> ⚠️ **P1 是回归**: 9.9.3 期已按用户拍板修好的白名单被 **9.9.6 升级覆盖** (`rg 'token-usage.yaml' delivery-gate.cjs` 现 0 命中) → 催生 P5 (patch 台账)。
> 新增: **P5** 升级覆盖本地 hook 修复无台账 · **P6** tdd-evidence 八字段必填 vs backfill 无 red 阶段的现实冲突 (9.9.6 加严所致, 2026-07-25 dry-run 实测当前 main = block) · **P7** 量化 AC 必先核基线 (批次3 REWORK 根因固化)。
>
> **P8 (2026-07-25, critic F1 分出)**: 截断/瞬断导致 `SubagentStop` 事件根本没被写入 (batch1 role=generator `ac31263f6412` = 8 Start/**0 Stop**, 亲验) — 这不是 gate 判据问题而是**事件采集缺口**, 指向 `subagent-tracker.cjs` 与平台生命周期钩子。本 sprint 的 W2 只放行"有 Stop 的 resume"(4/2/末次Stop), 截断场景继续走 `skip_impl_subagent_check` 显式释放 (不推翻 compound/2026-07-22 决策)。**待修**。
>
> **2026-07-28 新增 P10-P12** (撰写 9.9.6 sprint design §12 时识别, 均为 hook 层, 本刀零 hook 改动):
> **P10** critic 轮次全文字面计数可被正文讨论污染 (自检当场抓获) · **P11** 机器契约在 gate 源码与
> design 模板注记块双写、无单一真相源 · **P12** 派工时序只落约定无机械强制 (B-m1 = 扩展
> `subagent-worktree-check.cjs` 在派工关口拦)。相关教训见
> `compound/2026-07-28-learning-reserved-ac-labels-silent-exemption.md`。
>
> **P9 (2026-07-25, 实测撞上)**: `subagent-worktree-check.cjs:107` 对 Refactor/System + 写文件 subagent **无条件**要求 `isolation: worktree`, **无任何豁免出口** (亲验全文 135 行, 不读 _index 任何字段)。但当改动对象在项目 repo **之外**时 (如 `~/.claude` harness 自身), worktree 既无隔离效果 (不覆盖 repo 外文件) 又**禁止**写入这些路径 → 合法任务被死锁。本次处置: 用户显式批准把 harness sprint 降为 Feature 路径 (记 `route_history`)。**建议修复**: 加 `_index` 字段 (如 `harness_target_outside_repo: true`) 或识别 "改动清单全在 repo 外" 时放行并要求备份证据。**待修** (鸡生蛋: 修它需写 hook, 写 hook 又被它拦 → 需主 agent 直做那一步)。
>
> 🔁 **2026-07-28 二次撞上 (优先级上调)**: 9.9.6 sprint 执行 G1-G5 (双端模板/references/rules 文档改动, 落点含 `~/.claude` 与 `~/.codex`) 时 spawn generator 再次被无条件 block。**这次没有降级路径可走** —— 上次的处置是把 sprint 降为 Feature, 但本次用户已拍板该范围并入 System sprint, path 不可降。实际处置: 用户显式批准主 agent 直做 (记 `route_history`), 改安装态前逐个备份 12 个文件 (`~/.claude/backups/*.pre-g1g5-20260728T024943Z`, `~/.codex/backups/` 同)。
> **两次撞上的共同形态**: 红区 + 改动对象在 repo 外 = 门禁要求的隔离手段对该对象无效, 却仍阻断唯一合法执行路径。**它把铁律[零写入]的执行面变成了"要么违规、要么不做"的二选一, 每次都靠人拍板放行 —— 这正是门禁不该有的形态。** 建议修复优先级从"待修"上调为**下刀必修**。

## P13 · 已完成 sprint 的 review 绑定与台账更新存在时序陷阱 (2026-07-28, R6-F5 critic 核出)

- **现象**: `.ai_state/harness-patches.md` 是 git 跟踪文件, 既不在 `validateReviewBinding` 的漂移白名单 (cjs:471-491), 又被 `isLightShipFile` 永判非轻 (cjs:889/py:1188)。两条规则叠加的后果: **review 绑定 commit 之后再补一笔台账, 立即变成 "unreviewed .ai_state drift" 并卡死 ship**。
- **为什么会自然发生**: 台账的语义是"每处安装态改动都要登记", 而安装态改动往往在 review 之后的修复轮才出现 (reviewer 提出的问题要改 hook/rules) → 补台账是**正确行为**, 却触发阻断。
- **本次处置**: 不改 hook, 改工序 —— checklist G6 加 `ordering_constraint`: 台账收口 → 进 reviewed commit → 冻结; review 期间新增安装态改动须重走绑定。
- **建议修复**: 要么把 `harness-patches.md` 纳入 `validateReviewBinding` 的受控漂移白名单 (代价: 台账可在 review 后被静默改), 要么让 gate 在检出该文件漂移时给出"重走绑定"的可执行解锁链而非泛化 drift 报错 (倾向后者 —— 保持 fail-closed, 只修解锁动作)。**待修**。

## P1 · delivery-gate 与 token-usage hook 的文件名/易变性错位 (2026-07-24, batch1 ship 实测死结)

- **现象**: delivery-gate.cjs 的 post-review 白名单只认 `sprints/{slug}/token-usage.jsonl` (delivery-gate.cjs:409), 但 token-usage hook 实际写 `token-usage.yaml`, 且**每次 Stop 都先于 gate 改写** (updated_at + totals 累计)。
- **后果**: 全契约 ship 结构性死锁 — 把 token-usage.yaml 钉进 review-manifest → Stop 时 hook 先写后验, 哈希必落后一拍 (`review-manifest hash mismatch: token-usage.yaml`, 2026-07-24 实测); 不钉 → working drift 不在白名单, 同样 block。任一状态均无解。
- **同类隐患**: evidence.yaml 被 manifest 强制钉住, 但 PostToolUse hook 会因 ship 阶段的验证命令 (如 merge 后复跑 bun test) 继续追加 → 同样的钉住-即-失效。
- **建议修复** (二选一): (a) 白名单加 `token-usage.yaml` 且把 token-usage/evidence 这类 hook 持续维护的记账文件从 manifest 必钉集合中排除 (它们是过程记账, 不是被审对象); (b) token-usage hook 改写 `.jsonl` 对齐 gate。
- **本次处置**: 档案全部诚实落盘 (review-manifest/tdd-evidence/binding/ARCHITECTURE), 死结经用户拍板走 idle 释放 (先例: compound/2026-07-21-decision-e3-2-3-idle-release.md)。


> ✅ **2026-07-25 已修复** (sprint 2026-07-25-harness-gate-p1-p4): 见 `.ai_state/harness-patches.md` 第 1 条 (含可执行复核命令) · 源已入 Rlues `vibeCoding/{claude,codex}/9.9.6/` (commit b4f45eb) 防升级再蒸发 · G1-G5 dry-run 实跑证据见该 sprint `tdd-evidence.yaml`。

## P2 · generator 生命周期 "恰一次 Start/Stop" 与断点续跑不兼容 (2026-07-24, batch1 实测)

- **现象**: validateGeneratorChain 要求 generator agent_id 恰一次 SubagentStart/Stop; API 瞬断 (本会话 7 次) 后 SendMessage 断点续跑, 同一 agent_id 产生 19 Start/6 Stop — 真实工作痕迹反而不合规。
- **建议**: 放宽为 "≥1 Start 且末次事件为 Stop 且 assignment 时间戳落在首 Start 之后"; 或续跑事件带 resume 标记。
- **2026-07-24 batch2 复发**: 瞬断 2 次 SendMessage 续跑 → 同 agent_id 多次 Start/Stop; 且 assignments 握手因 generator 写入被 worktree 硬隔离 (见 P4) 根本无法写进主仓共享 JSONL — 恰一次契约在 worktree 隔离模式下结构性不可满足, 修复优先级建议提升。
- **本次处置**: skip_impl_subagent_check=true 诚实豁免 (证据链完整留档: assignments + events + 10 worktree commits), 先例 compound/2026-07-22-decision-e3-4-generator-truncation-subagent-check.md。


> ✅ **2026-07-25 已修复** (sprint 2026-07-25-harness-gate-p1-p4): 见 `.ai_state/harness-patches.md` 第 2 条 (含可执行复核命令) · 源已入 Rlues `vibeCoding/{claude,codex}/9.9.6/` (commit b4f45eb) 防升级再蒸发 · G1-G5 dry-run 实跑证据见该 sprint `tdd-evidence.yaml`。

## P3 · delivery-gate 按 shell cwd 解析 .ai_state, worktree 内误拦 (2026-07-24, batch2 实测)

- **现象**: 主 agent Bash `cd` 进 subagent worktree 查进度后 cwd 持久化; Stop 时 delivery-gate 以 cwd 为根解析 `.ai_state`, 在 worktree 里找 batch1 的 `evidence.yaml` (gitignore 白名单文件, worktree 检出必然不存在) 而 block。polish subagent 也复现: 对 /tmp 的无关 Write 都触发同一 complaint。
- **建议**: gate 解析项目根用 `git rev-parse --git-common-dir` 归一到主仓, 而非 process.cwd(); 或检测 cwd 在 `.claude/worktrees/` 下时跳过 ship 验证 (worktree 不是 ship 面)。
- **本次处置**: cd 回主仓即解; 工作纪律改为查 worktree 一律 `git -C <path>`。


> ✅ **2026-07-25 已修复** (sprint 2026-07-25-harness-gate-p1-p4): 见 `.ai_state/harness-patches.md` 第 3 条 (含可执行复核命令) · 源已入 Rlues `vibeCoding/{claude,codex}/9.9.6/` (commit b4f45eb) 防升级再蒸发 · G1-G5 dry-run 实跑证据见该 sprint `tdd-evidence.yaml`。

## P4 · polish_worker 的 Edit/Write 被硬隔离在自有 worktree, 无法履行"唯一写者"职责 (2026-07-24, batch2 实测)

- **现象**: polish-worker 带 worktree 隔离 spawn 后, 对主仓 .ai_state 与目标 generator worktree 的写入均被拒 (`This agent is isolated in the worktree ...`); 它被迫把目标分支 merge 进自己的 worktree 作业, 产物靠"再合并回 main"传递。可行但多一跳分支, 且 architecture/cleanup-pass 等主仓档案更新被间接化。
- **建议**: polish 阶段 spawn polish-worker 时**不加 isolation** (它本就是串行唯一写者, 无并行写冲突面), 或平台支持指定"作业于既有 worktree"; skill/stages 文档同步注明。
- **本次处置**: 分支合并传递成功 (979e004 → merge 2a3949e), 无产物丢失。


> 🟡 **2026-07-25 重定界并部分处置**: 平台 isolation 语义 hook 改不了 → 改的是编排知识: `skills/pace/references/stages.md` polish 段已注明 polish_worker 不加 isolation、改动对象在 repo 外时同理不用 worktree (harness-patches 第 8 条)。**衍生出 P9** (worktree 强制检查无豁免出口) 仍待修。

## P10 · critic 轮次判据是全文字面计数, 讨论该契约的 design 会虚增轮次 (2026-07-28, 撰写 §12 时自检抓获)

- **现象**: `validateCriticRounds` (cjs:599-607) 的判据是
  `const rounds = (design.match(/Critic Findings/g) || []).length` —— **全文匹配, 无位置约束**。
  任何**讨论**该契约的 design 正文 (包括本轮新增的 design §12.1 第 3 条、以及它要修的模板注记块本身)
  只要原样写出该字面串, 就会被计成一轮 critic → Refactor/System 地板 2 被平凡满足, 检查形同虚设。
- **亲验**: 本轮撰写 §12 时初稿曾原样写出该串作正则示例, 自检时抓获; 改用转写
  (「字面 `Critic` + 空格 + `Findings`」) 后, `grep -c 'Critic Findings' design.md` 仍为 5,
  确认新增 100 行正文零污染。**这是靠人自觉规避的, 下一个不知情的写者必然复发。**
- **建议修复**: 计数锚定到 **2-3 级标题行**内出现该字面串 (与既有 Round 1-5 段头体例一致),
  例如 `^#{2,3}\s.*Critic Findings`; 正文提及即不再计数。两端对称改。
- **风险**: 存量 design 若有非标题形态的轮次记录会一次性失效 → 需先扫历史 sprint 确认体例一致。
- **本次处置**: 未改 hook (本刀零 hook 改动)。design §12.7 第 1 条留痕, 转写规避。**待修**。

## P11 · 机器契约双写必漂: 模板注记块与 gate 源码无单一真相源 (2026-07-28, §12 设计时识别)

- **现象**: 本轮修法是把 gate 的机器判据抄进 design 模板的注记块 (AC19), 解决"隐藏考纲"。
  但契约由此**写在两处** —— gate 源码是执行真相, 模板注记块是给人看的副本, 两者无任何机械同步。
  gate 演进 (本文写作期间它刚加过熔断器, ±200 行) 而注记块不动, 就从"隐藏考纲"退化成"错误考纲",
  比不写更坏 (人会照着过期契约写 AC 并信以为真)。
- **已采取的缓解 (不是根治)**: 注记块以**函数/常量名**为锚而非行号 (行号必漂);
  尾行标注同步日期; 把"gate 判据变更须同步模板注记"写进注记块自身。
- **建议根治**: 契约单源生成 —— gate 源码内以结构化注释/常量导出判据摘要, 由脚本生成模板注记块,
  CI/validator 比对生成物与入库物一致 (漂移即 fail)。属新机制, 需先确认第二消费者存在
  (目前只有 design 模板一个消费者 → 按铁律[反过度工程]暂不抽象)。
- **本次处置**: 只落缓解。**待评估**, 触发条件 = 出现第二个需要同步该契约的文档面。

## P12 · 派工时序无机械强制, 只落约定 (2026-07-28, 消费侧 ledger-debt-batch 实测起因)

- **现象**: stage 翻 impl 晚于首次派工时, 门禁从翻转那一刻起对所有在飞写者即时生效
  (P3 修复后 gate 从主 checkout 解析 `_index`, worktree 内写者同样受支配) → 三个写者整轮撞墙。
  本轮修法 (design §12.2) 只把时序规则落进 `stages.md` step 0 与 `orchestration.md`, **靠自觉**。
- **建议机械化 (B-m1, 推荐)**: 扩展 `subagent-worktree-check.cjs` (已挂 PreToolUse `Agent`,
  是天然的派工关口): spawn generator 时若 `stage ∉ {impl}` 或本 sprint design 的 AC 段解析为 0 条
  → block spawn 并报可执行解锁链。优点是在**正确的边界** (派工时刻) 拦, 不碰 `_index` 写入路径。
- **已否决的备选 (B-m2)**: delivery-gate 在 `_index.md` 写入时 diff frontmatter, 在飞写者存在则拒改
  stage。缺点: `_index.md` 已知有 lost-update 与 hook churn 问题; 写者崩溃后永无 Stop → stage 永锁,
  必须再设逃生口, 复杂度不成比例。
- **本次处置**: 约定先落 (AC22), 并给出派工前单条自检命令降低违约概率。**待修** (hook 改动, 下刀)。
