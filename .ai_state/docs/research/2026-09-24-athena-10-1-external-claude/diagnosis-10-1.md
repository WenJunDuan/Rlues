# Athena 10.1 现状诊断：两个仓库的真实数据

> 取数日 2026-09-24，只读统计，没有改任何文件。quantum-agent 的凭据文件没有读。
> 版本号按你的决定定为 **10.1**（CHANGELOG 头注写明"用户指定，跳过 10.0"）。

## 1. 结论

- `.ai_state` 的主要负担不是正文，而是**过程记账**：一半左右的提交只在记账，每个 sprint 约 15 个过程文件里设计稿只占两成。
- **手工梳理撑不住**：quantum 9-23 刚把热层从 68 个 sprint 梳到 11 个，当天就回涨到 14 个。归档必须在 ship 时自动发生。
- **门禁在教 agent 怎么"应付"它**：quantum 的 proposals 里有 11 条「门禁坑」，全是 review 绑定协议的操作顺序和回执格式。这部分协议太重，应该收成一条命令。
- **门禁修复赶不上踩坑**：Q12 验收 32 条，只有 20 条生效，未生效的 9 条全部卡在"上游还没做"（没合并的分支、pending 切片、周末处理）。同一条修复要在 cjs、py、Pi 三份代码里各改一遍，是修复慢的结构原因。
- **规划也在膨胀**：Rlues 里的规划散在 7 处，和 `.ai_state` 的问题同形。

## 2. quantum-agent `.ai_state` 实测

| 指标 | 数值 | 说明 |
|---|---|---|
| 仓库提交（7 月起） | 1,545 | — |
| 动到 `.ai_state` 的提交 | 997（65%） | — |
| 9-16 以来只改 `.ai_state` 的提交 | 546 个里 254 个（**46.5%**） | 提交前缀 `ai-state:` 一类共 208 条 |
| 单日提交峰值 | 9-22：120；9-23：139 | 记账提交放大了提交频率 |
| `.ai_state` 文件数 | 4,318（git 跟踪 3,520） | txt 1,221 · md 954 · json 770 · jsonl 236 |
| git 跟踪体积 | **21.9 MB** | 冷层也在主分支里 |
| `archive/sprints` | 102 个 sprint · 3,097 个文件 · 20 MB | 已归档，但仍随每次 clone 下载 |
| `.ai_state/docs/archive` | 1.9 MB，含原始执行日志（例如 `codex-exec-stdout.log` 311 KB） | 原始日志不应入库 |
| `.snapshots/config-events.jsonl` | 336 KB，被 git 跟踪且持续改动 | 两个仓库的工作区都显示它被修改 |
| `.runtime` | 21 MB | gitignored，没有容量上限 |
| 热层 sprints | **14**（9-23 当天梳理后是 11） | 回涨很快 |
| compound | 61 档（决策 35 · 教训 20 · 技巧 5 · 探索 1） | 决策档占多数，没有"被取代"标注会越积越多 |
| `_index.md` | 8.5 KB | `cc_version` 记 2.1.263（Rlues 记 2.1.236，两边都过期）；`platform_features` 与探测结果不一致 |
| `harness_target_outside_repo` | **true，从 9-10 起一直开着** | 这个开关会免掉 worktree 要求。开关没有过期时间，是**门禁旁路风险** |
| proposals.md | 130 行 / 28 KB（已梳理过一次） | 其中「门禁坑」11 条 |

### 单个 sprint 的过程文件（readonly-config-stats，共 48.8 KB）

| 文件 | 大小 | 问题 |
|---|---|---|
| design.md | 9.7 KB | 合同本体，保留 |
| session-log.md | 7.0 KB | 叙事化，和 git log、evidence 重复 |
| evidence.yaml + tdd-evidence.yaml + evidence/*.txt | 12.9 KB | 两份证据账 |
| review-packet.md + reviews/_native/*.json ×2 + implementation-review.md | 10.0 KB | 同一次审查存三处 |
| subagent-events.jsonl + subagent-log.md + subagent-assignments.jsonl | 6.2 KB | 同一事件存三份 |

**design 占 20%，过程记账占 80%。**

### 门禁坑 11 条（review 绑定协议的操作手册）

bind 恒拒要 supersede 再 prepare · 采集器只认特定命令形态且必须是第一条语句 · 每个 run 要全新 reviewer · tracker 要求新的 SubagentStart · 老 System sprint 别走 ship 门禁 · dispatch 和 result 回执 schema 不同 · bind 只接受 UUID · result.json 必含三字段且只有一行 VERDICT · 90 轮上限续派不入账 · AC 行首锚定口径反转 · `cat` heredoc 写出 0 字节。

这些都是 agent 为了"通过门禁"要记住的规程，而不是产品质量要求。

### Q12 验收（2026-09-23）

32 条：生效 20 / 部分生效 2 / **未生效 9** / 无法判定 1。未生效的全部是上游没做：切片 5 只在未合并分支 `grok/writer-provenance`，切片 6 pending，另有 4 条误拦（跨仓 push、`design_changed_after_impl`、features_count、承诺闭合调参）停在提案。

## 3. Rlues 实测

| 指标 | 数值 |
|---|---|
| 9 月提交 | 118，其中 73 个动 `.ai_state`（62%） |
| 当前 sprint | 切片 5 `writer-provenance`，stage=impl，grok 施工，**已交接 3 天**，分支未合并 |
| q12 roadmap | 9 片：完成 6 / pending 3（5、6、9） |
| 规划散落位置 | `next-version/proposals.md`（约 51 条，按日期追加 4 节）· `brainstorm.md`（已被取代）· `proposals.md`（P1–P13）· `harness-patches.md`（263 行）· `roadmap/q12` · `compound/` · quantum 侧 `queue.md`「待上游」与 `proposals.md` |
| `_index.md` | 当前状态段有 5 行重复死锚；README 的当前状态停在 9.9.8 |
| `.runtime` | 35 MB（3 个 12 MB 的 q12 输入包） |

## 4. 由数据推出的 10.1 调整（相对上一版方案）

| # | 数据 | 调整 |
|---|---|---|
| D1 | 门禁坑 11 条 | **新增 M10：review 一条命令**。`athena review` 内部完成 prepare → 派发 → 绑定 → 收取；reviewer 只回 verdict + findings；run id、回执、supersede 全由工具处理。门禁坑清单应当归零 |
| D2 | 每 sprint 三份重复账 | sprint 目录只剩 4 个入库文件：`design.md` · `evidence.yaml`（合并 tdd-evidence）· `review.json` · `log.md`（≤20 行）；subagent 事件只写 `.runtime` |
| D3 | 热层当天回涨 | ship 自动归档改成**硬行为**（不是提醒）；热层上限 3 |
| D4 | 冷层 21.9 MB 随 clone 下载 | **新增 M11：冷层出主树**。二选一：①按月打包 `archive/YYYY-MM.tar.zst` 入库，展开目录不入库；②归档移到孤儿分支 `ai-state-archive`（`git worktree` 按需挂载）。推荐①，查询简单、审计 sha 不变 |
| D5 | 原始日志、snapshots 入库 | `.gitignore` 增加 `*.log`、`*-stdout.*`、`.snapshots/`；已跟踪的执行 `git rm --cached`（**不可逆操作只动索引，文件保留**） |
| D6 | 旁路开关常开 2 周 | **新增 M12：旁路开关带过期**。`harness_target_outside_repo` 这类豁免字段改成 `{value, until, reason}`，过期自动失效，session-start 提示 |
| D7 | 记账提交占 46–65% | stage 转换不单独提交；ship 一次提交带齐状态。目标 ≤20% |
| D8 | Q12 未生效 9 条都卡在上游 | 见 §5 分流 |
| D9 | 规划散落 7 处 | Rlues 只留一个 `queue.md` 作为 harness 待办入口；quantum 侧「待上游」只写一行指针指到 Rlues |
| D10 | 版本记录不一致 | 平台版本和能力位移到 `.runtime/probe.json`，每次 session-start 探测，不再手写进 `_index` |

## 5. 10.1 之前的收口顺序

| 序 | 动作 | 理由 |
|---|---|---|
| 1 | 核验并合入切片 5（`grok/writer-provenance`），走完已设计好的 review/ship | 已做完三轮设计审查和施工，放弃代价最大 |
| 2 | 小修只改两处、只修 3 条天天踩的：跨仓 push 与 heredoc 正文误判、`design_changed_after_impl` 误触发、承诺闭合句式 | 天天误拦，等不到 10.1 |
| 3 | 切片 6、9 **不再单独做**，内容并入 10.1 门禁核：6 = 只读会话 Stop / 架构检查看已审范围；9 = 发行一致性，本来就是单源构建要解决的 | 避免在即将替换的代码上做两遍 |
| 4 | features_count 误计不修，10.1 直接删除 `counts` | 字段没有消费者 |
| 5 | 开 10.1 分支 | — |

## 6. 10.1 验收指标（用这两个仓库量）

| 指标 | 现在 | 10.1 目标 |
|---|---|---|
| 只改 `.ai_state` 的提交占比 | quantum 46.5% / Rlues 62% | ≤20% |
| 单 sprint 入库过程文件 | 约 15 个 / 约 49 KB | 4 个 / 设计稿以外 ≤15 KB |
| 热层 sprint 数 | 14 | ≤3 |
| `.ai_state` git 跟踪体积 | 21.9 MB | ≤3 MB（冷层打包后） |
| `_index.md` | 8.5 KB | ≤3 KB |
| 门禁坑条目 | 11 | 0（全部由工具吸收） |
| 同一门禁逻辑的实现份数 | 3 | 1 |
| 门禁修复从提出到生效 | 数天到数周（Q12 9 条未生效） | 单点修改 + fixture，当天可发 patch |
