---
schema_version: 1
sprint_slug: "2026-08-27-athena-9-9-8"
mode: "independent-design-challenge"
packet_source: "review-packet.md"
source_design_sha256: "4d40949729d9e6c4ce366ddf2e3acd82808b91278e2c421e2b5ad706fe88fb53"
design_sha256_verified: true
reviewer: "claude-fable-5 (Cowork, 非设计作者会话)"
review_date: "2026-08-27"
finding_counts: {P0: 0, P1: 4, P2: 3, INFO: 1}
---

# Design Review — Athena 9.9.8 Thin PACE Control Plane

按 `review-packet.md` 执行。design.md hash 已机械核对一致；本地实证核对了 CC/CX 9.9.6 全量文件、delivery-gate.cjs、`_index.md`、telemetry 占比与 agents frontmatter；外部事实按铁律[证据与出处]双源核验（官方 CHANGELOG 优先于聚合站）。

总评：方向正确。删作者自审、一次原生多维 review、hook 红黄绿、ai_state 三层分级，与 Anthropic AI-native SDLC playbook（产物链、下一阶段消费上一阶段产物、review 前移）及 CC/CX 官方 best practices 一致。四个 P1 全部是"设计与 2026-08 harness 现实的时序/口径缺口"，可在 design 修订解决，不需要推翻架构。

## Findings

### F1 [P1] CC 原生 review 已是后台 subagent，设计流程按同步叙事 — 重蹈 9.9.6 P0-2 的同款结构风险
- AC: AC3/AC4 · 章节: 目标流程、一次多维 review
- 事实: 官方 CHANGELOG **2.1.221 "Changed `/code-review` to run as a background subagent"**、**2.1.223 "`/review` alias of `/code-review`"**。后台 = 结果在后续 turn 以完成通知到达，与 9.9.6 review 报告 P0-2（背景 subagent 结果不可能同轮收齐）同一机制。
- 反例: 主 agent 发起 `/code-review` 后在同轮等待结果 → Stop/pace-continuator 造成活锁，或主 agent 空转烧 token。
- 修: design 把"一次 review 请求"显式定义为**异步里程碑**：发起 → 本轮允许正常结束 → 完成通知轮校验/落盘结果 → gate 只认"结果文件存在 + packet/diff hash 匹配"，不认时序。双端 fixture 增加"后台完成通知轮"用例；Stop hook 对 pending review 放行而非 block。

### F2 [P1] AC11 不可证伪：控制面 token 无口径，且切片 3 可能在对比前销毁基线
- AC: AC11 · 章节: 验收标准、`ai_state` 三层
- 事实: 现仓库 telemetry 实证是字节大头（token-usage.yaml 单文件最大 796KB）。切片 3 把 telemetry 移出 Git 并设 20 次/14 天 retention —— 若先落切片 3，AC11 的"对比基线"数据可能已被 retention 清掉。"控制面 token"在 design 中无定义（思考 token？review subagent？hook 注入的续跑 turn？各算不算）。
- 修: design 增补两条：(a) 口径定义 —— 控制面 token = 产物为 `.ai_state` 记账/review/route 类文件的 turn + review/critic 类 subagent 会话 + hook 注入 continuation turn 的输出 token，按 token-usage.yaml 的 per-turn 标签机械归类；(b) 实施顺序约束 —— 切片 3 迁移前先从 9.9.6 代表性 sprint 导出冻结 baseline artifact（可放 ignored runtime，但显式豁免 retention）。

### F3 [P1] 目标复核无终止规则；原生 review 结果文件的作者与转录完整性未指定
- AC: AC3/AC4/AC6 · 章节: 一次多维 review
- 反例 1: 复核发现新 P0 → 再修 → 再复核……无上界，passN 换名复活。
- 反例 2: 原生入口（CC /code-review、CX /review）在会话流里输出 findings，不会自己写带 frontmatter 的 `reviews/implementation-review.md`。若由主 agent 转录，正好落回 9.9.6 明令禁止的"主 agent 伪造 findings"暴露面 —— 而 9.9.8 同时还删掉了 read-only 角色的 assignment 绑定，gate 无从校验。
- 修: (a) 终止规则对齐 hook 收敛条款：目标复核同因 ×2 仍出新 P0 → 交还用户，禁止无界复核；(b) 结果落盘二选一并写入 design —— fallback reviewer agent 直接写结果文件；或主 agent 转录时必须附原生 review 原始输出的引用（CC transcript / CX `/export` 产物路径）作为 evidence，gate 校验 `review_run_id` 与该引用存在。

### F4 [P1] 承重事实未钉版本，且部分只有二手源 — 正是 9.9.6 review 要升铁律的"文档层不可作一手事实"
- AC: AC7/AC8 · 章节: Hook 严格度、官方证据与边界
- 事实: design 三个承重断言全部版本敏感：同事件 hook 并发语义、"CX 只执行 command/MCP hook，prompt/agent handler 跳过"、原生 review 入口形态。`_index` 记录 cc 2.1.211 / cx 0.145.0，而 CC 官方 CHANGELOG 已到 2.1.246；CX 0.146–0.149 的 async hooks/MCP 调用、agents dashboard 等目前**只有聚合站二手源**，github releases 首屏抓取只见到 rust-v0.144.0（标记: 待验证）。design 引用全部是 docs URL，无 schema/源码/tag 双源。
- 修: design 增加 target harness 版本 pin（如 CC ≥2.1.246 / CX 待验证后钉），承重断言逐条补双源（源码 dispatch 点或 release tag）；impl-entry 前按 pin 版本重验三断言，验不过按黄区降级处理而非带病实施。

### F5 [P2] "9.9.6 CC 只有 generator 命中 skills:[pace]" 与仓库事实不符
- AC: AC8 · 章节: 对 Grok 草案的修正、实现切片 2
- 事实（grep 实证）: `critic.md`、`architect.md` 同样有 `skills: [pace]`（architect 还有 architect-doc）。critic 在 9.9.8 删除故无碍；**architect 保留**于 R/S 独立挑战路径，其 pace 预加载去留未被决策。
- 修: 更正表述；显式决策 architect 是否保留预加载（挑战设计需要路由全景 → 保留可辩护，但要写出来）。

### F6 [P2] `_index` 12KiB 上限方向对、机制错位：超标主因是单条散文长度，不是条数
- AC: AC9 · 章节: `ai_state` 三层
- 事实: 现 `_index.md` 13.8KB 已超标，route_history 条数 =10（合规）但单条 200–600 字。"列表 ≤10 项 + 写入时截断"治不了这个，且静默截断销毁审计链，与铁律[证据与出处]冲突。
- 修: 约束改为"每条 ≤160 字节，溢出部分移入 `sprints/{slug}/route-note.md`，`_index` 留一行摘要 + 指针"；hook 做搬运不做丢弃。

### F7 [P2] "tasks 全绿 (Sisyphus)" 类话术已与 CC 2.1.233 脱节
- AC: AC7 · 章节: 实现切片 2（扫描面）
- 事实: 官方 CHANGELOG 2.1.233 —— todo/task 工具在 Opus 4.8 / Sonnet 5 / Fable 5 及更新模型上**已移除**。CLAUDE.md 铁律 1 与 stages 话术若被读成依赖 CC 原生 task 工具，在新模型上指向不存在的东西。
- 修: 切片 2 扫描面加一项：凡"tasks 全绿"类表述统一改指 `checklist.yaml` 自有文件；列入 dogfood 必测。

### F8 [INFO] 还能再删一层：自建 telemetry 采集可评估降级
- 章节: `ai_state` 三层、实现切片 3
- CC `/usage` 已含 per-loop 用量、原生 OTEL 遥测成熟；token-usage-collector / tool-trace 自建 hook 可评估降为"只补 harness 不给的字段"，进一步削 PostToolUse 记账面。另: 2.1.218 起 subagent 默认不再嵌套派发、2.1.217 并发默认上限 20 —— orchestration.md 的编排假设需同步。不阻塞 9.9.8，记为切片 3 的可选项。

## MISSING / EXTRA / DEVIATED

| 类 | 项 |
|---|---|
| MISSING | 后台 review 异步时序 (F1) · 控制面 token 口径与 baseline 冻结顺序 (F2) · 目标复核终止规则与结果转录完整性 (F3) · target harness 版本 pin 与双源 (F4) |
| EXTRA | 无。未来槽 A/B 已正确隔离为 opt-in 非默认热路径，不构成过度设计 |
| DEVIATED | "只有 generator 命中 pace" 与 agents frontmatter 实况 (F5) · AC9 的界与 `_index` 实际膨胀机理 (F6) |

## 复核确认（packet 十问中经得住的部分，一行带过）

一次 review ≠ mega-agent（原生入口 + 固定维度 + gate 接管机械项，成立）· packet hash/AC 双射机械可验（hash 本次实测一致）· polish 前移与 ship 义务不冲突（AC5 的 diff-hash block 封住后门）· Feature 取消固定 design review 未破坏设计先行（impl-entry spec-gate 仍在）· archive/catalog 无第二真相源（可重建 + ignored，成立）· 未来槽未动 runtime-verify 矩阵、LaaV 未入门禁（成立）。

修订路径: F1–F4 改 design → 重生成 packet（hash 更新）→ 无需第二轮独立挑战，作者修订即可 → `implementation_authorized` 可翻转。

VERDICT: CONCERNS
