---
sprint_slug: "2026-08-27-athena-9-9-8"
doc_type: "research"
created: "2026-08-27"
scope: "Anthropic AI-native SDLC / CC & CX harness 动向 / 提示词优化方向"
provenance_rule: "官方 CHANGELOG/发布页 > 官方 docs > 聚合站；二手源单独标记待验证"
---

# Research — 2026-08 Harness 扫描与 9.9.8 方向校准

供 9.9.8 design 修订与复盘使用。结论在前，证据表在后。

## 结论

1. **方向判定：9.9.8 "Thin PACE Control Plane" 方向正确，不需要调头。** Anthropic AI-native SDLC playbook 与 Athena PACE 是同构的：六阶段产物链（intent→spec→plan→build→test→deploy→maintain）≈ PACE 的 stage 链；"下一阶段消费上一阶段的已提交产物，而不是重演对话" ≈ 用户要求的"基于设计材料写 review 材料，不是教模型再看一次设计"。官方比 Athena 更瘦的地方恰是 9.9.8 要删的：官方用 REVIEW.md（稳定策略）+ 原生 Code Review 承载审查，不自建 critic/evaluator 编排；官方 CLAUDE.md 要求"一页以内"。
2. **token 浪费的三个来源按大小排序：固定仪式（critic 轮次 + 2+1 review + passN）> hook 注入的续跑/记账 turn > 材料重复读取（reviewer 重读 design、evaluator 重读全家桶）。** 9.9.8 三切片正好逐一对应，砍的顺序也对。
3. **一个新时序事实必须进设计：CC 原生 review 自 2.1.221 起是后台 subagent。**"一次原生 review"必须按异步里程碑设计，否则复刻 9.9.6 P0-2（详见 design-review F1）。
4. **文档检索问题（项目多→文档多→查找慢）：现阶段用"有界 _index + 冷归档 + 可重建 catalog"够了，不要上 SQLite/embedding。** 3.6MB/243 文件的仓库，字节大头是 telemetry（单个 token-usage.yaml 最大 796KB），查找税来自平铺历史，不来自缺索引技术。先归档 + 截断，实测仍慢再升级。
5. **模型/effort 路由是下一个最大的省钱杠杆，但必须 eval 先行**（两家官方口径一致：用代表性任务验证更低 effort，再改默认）。

## Anthropic AI-native SDLC playbook 要点 × PACE 对照

来源: claude.com/blog/the-ai-native-sdlc-playbook（2026-08）

| Playbook | PACE 现状 | 9.9.8 动作 |
|---|---|---|
| 产物链: 每阶段读上一阶段已提交产物 | design→packet→review 派生链（9.9.8 新增） | 已对齐，保持 |
| review 前移: plan mode 先审 plan.md 再写码 | impl-entry spec-gate | 已对齐 |
| agent 自验证（test/build/screenshot）先于人审 | runtime-verify | 已对齐 |
| REVIEW.md = 稳定 review-only 策略，按严重度排序 findings | athena-review 的 2+1 编排（将删） | 改为 REVIEW.md/AGENTS.md scoped rules + 一次原生请求 |
| "layers of agentic review" 指 deploy 前多层，非要求自建多轮 | 9.9.6 的 pass1/2/3 | 官方 harness 内部多 agent 不计入 Athena 轮次 —— design 表述正确 |
| CLAUDE.md ≤1 页；重复犯错才加一条 | CLAUDE.md 3.2KB 达标 | 保持，别再长 |
| hooks 承载不可协商项，其余交模型 | hook 过宽（rg 误报、双 block） | 红黄绿分级，方向一致 |
| eval 门禁: CLAUDE.md/skill/hook 变更跑 20–50 个真实任务回归 | validate-athena 静态断言 | **缺口**: Athena 只有静态门禁；9.9.8 AC11 的对照实验就是第一版 eval，值得沉淀成常设机制 |

## Claude Code 动向（官方 CHANGELOG 双源核验）

| 版本 | 变更 | 对 Athena 的含义 |
|---|---|---|
| 2.1.221 / 2.1.223 | `/code-review` 改为**后台 subagent**；`/review` 成为其别名 | "一次原生 review"必须异步化（design-review F1，P1） |
| 2.1.233 | todo/task 工具在 Opus 4.8 / Sonnet 5 / Fable 5+ **移除** | "tasks 全绿"话术需改指 checklist.yaml（F7） |
| 2.1.232 / 2.1.218 / 2.1.217 | subagent 默认 fork；默认不嵌套派发；并发上限默认 20 | orchestration.md 假设需同步（F8） |
| 2.1.237 | 内置 "Concise" 输出风格（结果先行、跳过铺垫） | 免费省 token，安装态可默认开启 |
| 2.1.243 | `/usage` 增 per-loop 用量拆分 | 自建 token 采集可评估降级为补充（F8） |
| 2.1.234 | auto mode 对已 compact 会话修复；用量限额重置自动续跑 | 长 sprint 依赖 harness compaction 更可靠，compact-snapshot/restore hook 的必要性下降，可列观察项 |

## Codex 动向

一手确认（github releases 首屏）: 0.144.0（2026-07-09）—— `/review` branch picker 加速、automatic review 指令改进、compaction 修复。

二手源（releasebot，**待验证**，github releases 抓取首屏未见 0.146+）:

| 版本 | 变更（待验证） | 若属实的含义 |
|---|---|---|
| 0.148.0 | `/export` 导出会话 markdown；`codex exec fork`；**异步 hooks 支持调用 MCP 工具** | `/export` 可作 review 转录 evidence（F3 修正的现成载体）；异步 hook 若实装，"CX 只执行 command/MCP hook"断言需按新版本重验（F4） |
| 0.147.0 | Agent Plugins 多目录；MCP 2026-07-28 协议；`--approve-for-me` | 分发形态可从"装文件"演进为 plugin，9.9.9+ 议题 |
| 0.149.0 | agents dashboard、跨会话消息队列 | 编排观测靠 harness，subagent-tracker 记账面可再减 |
| 0.144.6 | GPT-5.6 Sol/Terra/Luna 上下文修正为 272k | 模型路由表数据点 |

## 提示词/上下文工程官方口径（两家一致处 = 高置信方向）

- Anthropic effective-context-engineering + CC best practices: 上下文是有限资源；删模型本来就会做的指令；确定性约束交 hook；高噪声探索进 subagent；优化对象是 system prompt+工具+检索整体。
- OpenAI GPT-5.6 guidance: 瘦 prompt、每条指令只写一次、控制增长的上下文、低 effort 用 eval 验证后下调。
- 共同含义: Athena 的root 宪法(3.2KB)已达标，**下一步瘦身对象不是 root prompt，而是 hook 注入文本、subagent 输入包、以及每 sprint 重复传入的稳定规则**（后者应下沉为 scoped REVIEW.md / AGENTS.md / rules 文件，一次安装长期生效）。

## 检索与文档增长（用户痛点 3）

分层结论（与 design 一致，补充实测依据）:

| 事实 | 数据 |
|---|---|
| 仓库总量 | .ai_state 3.7MB / 243 git 文件 / 22 sprint |
| 字节大头 | telemetry: token-usage.yaml 796KB+468KB, tool-trace 324KB+92KB（前四名全是） |
| `_index` 超标机理 | 13.8KB，route_history 条数合规但单条 200–600 字散文 |

动作优先级: telemetry 出 Git（一次性砍掉 ~45% 字节）→ 冷归档平铺 sprint → `_index` 按"每条字节上限+溢出搬运"截断 → 可重建 catalog.jsonl。全部是文件系统操作，零新依赖。SQLite/embedding 在此数据量下是过度工程（铁律[反过度工程]）。

## 不做清单（本轮再确认）

- 不自建 agent loop / compaction / 并行编排 —— 两家 harness 都已内置且在快速迭代，自建即负债。
- 不合并 26 skill（无痛点数据）、不建第二状态树、不上检索数据库。
- 不把 LLM 评分放进同步 hook 或 ship 门禁（LaaV 仅 opt-in 排序，见 design 未来槽 B）。
- 不在无 eval 的情况下下调默认 model/effort。

## Sources

- https://claude.com/blog/the-ai-native-sdlc-playbook
- https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle （未展开，备查）
- https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md （CC 事实一手源）
- https://github.com/openai/codex/releases （CX 一手源；0.146+ 未在首屏确认）
- https://releasebot.io/updates/anthropic/claude-code · https://releasebot.io/updates/openai/codex （二手聚合，标待验证）
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://code.claude.com/docs/en/best-practices · https://code.claude.com/docs/en/code-review
- https://developers.openai.com/api/docs/guides/latest-model · https://developers.openai.com/blog/custom-code-review-rules-for-codex
