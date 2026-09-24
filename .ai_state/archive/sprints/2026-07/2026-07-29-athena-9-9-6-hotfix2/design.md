---
sprint_slug: "2026-07-29-athena-9-9-6-hotfix2"
path: "System"
created: "2026-07-29"
last_updated: "2026-07-29"
document_status: "reviewed-and-implemented"
implementation_authorized: true   # 用户 2026-07-29 授权 Fable 直接实现 (含 F1-F8 修订)
baseline_release: "9.9.6"
target_release: "9.9.6-hotfix2"
roadmap_slug: "athena-9-9-6-hotfix2"
---

# Design — Athena 9.9.6 hotfix2 控制面减负

> 本稿合并用户现场数据、Codex 主线程审计、独立 architect/explorer 与官方平台合同。目的不是证明流程正确，而是给 Fable 5 一份可以直接反驳的改造底稿。确认前不进入 impl。

## 1. 结论

9.9.6 的根 prompt、SessionStart 和 skill catalog 已经明显压薄；`PACE + .ai_state` 不是主要性能问题。当前瓶颈已经转移为**控制面放大**：一个任务动作会触发多进程 Hook、自动明细账、重复状态提醒和跨文档契约；部分提醒还会制造额外模型轮次。

hotfix2 应保留 PACE、项目真相、fail-closed safety/spec/ship gate、TDD、独立 review 和 worktree 隔离；删除没有核心消费者的遥测、假强制协议和重复提醒。原则：**状态只保存决策，Hook 只强制边界，模型只为交付回合付费。**

## 2. 现场事实与前序意见

- `.ai_state` 共 13,039 行中，12,283 行是 Hook 自动账本；不能据此判断“文档多于代码”。
- 手写文档 756 行，产品代码 4,095 行，代码约为文档 5.4 倍。此前把自动 telemetry 当手写文档的判断作废。
- 真正成立的问题是提交与同步过碎：20 个 docs commit 对 5 个 feat/fix，且一场会话刷新 `next_action` 8 次；这不是铁律要求，而是流程执行偏差。
- 本次实际交付很重：删除感官链 11 文件；新增技能 7、审批 5、workflow 4 个 HTTP 端点；打通取消状态、互斥锁和 415 门；`http-server.ts` 465→235 行；测试 1,941→2,090，`tsc` 干净。
- `token-usage.yaml` 不直接调用模型，因此文件存在本身不消耗模型 token；但逐记录账本会重读 transcript、重算并重写全文件，一旦进入 diff/工具输出又会污染上下文。
- 先前建议继续成立：普通运行不保留 raw records；如业务报告需要，只在 ship/on-demand 生成 `by_stage/by_model` 聚合，原始诊断数据不得进入版本化项目状态。

## 3. 已确认问题

| 等级 | 问题 | 现场证据与影响 |
|---|---|---|
| P0 | 只读 agent 被判成写者 | `subagent-worktree-audit.py:71-77` 对未知 profile 默认 writable；本轮只读 explorer 已生成 unresolved `worktree-violations.jsonl`，`delivery-gate.py:344-390` 会在 ship 阻断。安全默认制造了假违规和补账。 |
| P0 | 9.9.6 基线并非全绿 | `python3 vibeCoding/scripts/validate-athena-9.9.6.py` 当前为 64 PASS / 2 FAIL，均指向 fresh CX 仍写入空 `openai_base_url`；设计与 config 现实漂移。 |
| P0 | 提示合同与 gate 真相相反 | gate 已把 `review-manifest` 改为全路径 opt-in（CX `delivery-gate.py:1593-1595`；CC `delivery-gate.cjs:996-1000`），但双端 design 模板仍写“R/S 必踩”，CX stages 同文档 `:115` 与 `:126-127` 自相矛盾，CC 缺 cleanup 时还错误提示“再补 manifest”。它直接催生无必要文书。 |
| P0 | 原始命令进入版本化日志 | 双端 evidence collector 把 Bash command 原文写入 `tool-trace.jsonl`，无 secret redaction，且仓库未 ignore；这既是噪声，也是凭据/敏感参数留存风险。 |
| P1 | token 明细是写放大主源 | 现存 token 文件合计约 133 万字节 / 3.6 万行；主 sprint 814,684 B / 1,596 records。核心 gate 不消费 raw records，唯一业务报表只需要聚合。 |
| P1 | 普通工具遥测收益极低 | 主 sprint `tool-trace` 887 行 / 330,843 B，而 `evidence.yaml` 只有少量真验证记录；本轮只读评估短时间内也自动生成约 10 万字节状态。 |
| P1 | `next_action` 职责冲突 | 它同时承载进度散文、状态机信号、breadcrumb、SessionStart、Notification、Stop continuator 和 re-route 锁；非空时 `index-updater` 直接跳过 re-route 检测，长文本又挤掉 breadcrumb 的 stage 义务。 |
| P1 | Stop 软提醒重复且有模型税 | Claude `pace-continuator` 在 `next_action` 非空时向 Stop 注入 context；其源码和平台 Stop 语义均说明可能续一轮。Codex 对仅 additionalContext 是否续轮未由官方合同明确，不能伪装对称；两端都没有核心消费者。 |
| P1 | Hook 配置存在空跑与并发假设 | Codex 每 prompt 约 2 进程、每 Bash 3、每写入 4、每 Stop 3；`index-updater` 在 prompt/Bash/MCP 上启动后直接 no-op。同事件 command hooks 两端均并发执行，配置顺序不是优先级。 |
| P1 | 所有角色都被绑定记账 | spawn-binding 握手冻结新 spawn→等 Start→写 assignment→发 BOUND，但 ship 只消费 generator 链；architect/critic/reviewer/explorer 的绑定纯属串行税。 |
| P1 | PreCompact 快照无恢复消费者 | `compact-snapshot` 每次复制完整 `_index.md`，PostCompact 却始终读取 live `_index.md`；现有 snapshots 约 223 KB，并曾进入提交。 |
| P1 | 路由地板把“跨模块”误当“需 roadmap” | 一个不可拆的跨模块不变量也会因“≥3 模块”被强制拆 roadmap；本轮用户明确要一个 sprint，却仍被规则迫使多建两份路线图文件。 |
| P2 | gate 可维护性过低 | 双端 gate 分别约 1,653/1,245 行，混合 PreToolUse、impl、ship、evidence、review、roadmap、worktree 和熔断；历史缺陷已呈现保留 AC 编号、隐藏考纲、死锁和双端漂移。 |
| P2 | Codex 配置手填模型元数据 | `model_context_window=1000000`、`model_auto_compact_token_limit=900000` 覆盖模型默认；官方配置说明 unset 使用模型默认。它会形成随模型演进漂移的第二真相，是否增加长上下文时延需 A/B 证实。 |

## 4. 哪些设计保留

- 保留 4 核心 + 5 条件 stage；问题在触发与重复表达，不在 stage 名称。
- 保留 `.ai_state/_index.md` 作为有界检索入口；删除 raw telemetry 不等于删除项目记忆。
- 保留 impl-entry spec gate、危险命令 gate、ship gate、真实运行验证和独立 review。
- 保留 writer worktree 隔离；只读探索与审查不需要 worktree，也不应产生违规账。
- 保留 Skills 渐进披露。官方合同表明 Skill 正文按调用加载；26 个 skill catalog 当前约 3–4 KB，不是首要瓶颈。
- 双端只要求语义强度一致，不伪造 hook/tool/config 对称。

## 5. hotfix2 目标架构

### 5.1 指令所有权

| 层 | 唯一职责 |
|---|---|
| `AGENTS.md` / `CLAUDE.md` | 结果优先、状态真相、安全边界、写入隔离等少量宪法级不变量 |
| `athena-dev` | 是否进入 PACE、路径与入口 stage 路由 |
| `pace/SKILL.md` | 路径全景与 references 索引，不复述 stage 正文 |
| `stages.md` | 每个 stage 的最小进入/退出义务 |
| `orchestration.md` | agent、writer ownership、worktree 与平台差异 |
| templates | 只提供可解析骨架，不解释 gate 正则、保留编号或内部字段 |
| hooks/gates | 机械执行；只返回当前角色能完成的一条解锁动作，不承担流程教学 |

只读回答、解释、评估、诊断默认不创建 sprint、不改 `_index`；只有用户明确要求持久化（本轮即是）才进入 PACE。这是 eligibility gate，不新增第七条路径。

### 5.2 状态合同

- `_index` 只存 `path/stage/current_sprint/current_roadmap`、权威 pointers 和少量机器控制信号。
- `next_action` 禁止自由文本，只允许既有枚举：`re-route`、`runtime-verify`、`review`、`polish`、`ship`、`rework_impl`、`next_roadmap_item:{slug}`；正常进度为空。
- breadcrumb 不再注入 `next_action`；只给 `stage/path/sprint + 当前 stage 2 条义务`，确保 240 B 内义务不被状态文本挤掉。
- 状态写入点限定为：入口路由、真实 blocker/用户决策/跨会话 handoff、ship 前收口。禁止为每次暂停、百分比或 stage 过渡单独 commit。
- roadmap 只在存在至少 2 个可独立验收、可独立 ship 的切片时触发；模块数只影响 System/Refactor 风险等级，不单独强制 roadmap。

### 5.3 Hook 热路径

| 生命周期 | hotfix2 默认行为 |
|---|---|
| SessionStart/PostCompact | 读取 live `_index` 的紧凑状态和异常告警；不复制 snapshot |
| UserPromptSubmit | 仅 breadcrumb；不启动 index 扫描 |
| PreToolUse | 仅危险命令、impl-entry spec 和 writer worktree 硬边界 |
| PostToolUse | 只对 validation command 写脱敏 `evidence.yaml`；普通 Bash/Edit/MCP 零遥测 |
| SubagentStart/Stop | 只对需要 ship 证明的 writer/generator 建最小 lifecycle；只读角色用平台原生结果 |
| Stop | 只留 delivery gate；删除默认 `pace-continuator` 与 token collector |

- `token-usage-collector` 退出普通 lifecycle，改为 release A/B 显式工具；若报告需要，仅输出无 records 的聚合摘要。
- 删除 `tool-trace.jsonl`、`subagent-log.md` 和 pre-compact 快照的默认生成；保留真正被 gate 消费的 validation evidence、writer lifecycle 和 worktree violation。
- re-route 文件数改用与 ship 相同的 Git 现场变更集，在自然检查点计算，不再依赖每工具 trace。
- 同事件 hooks 必须幂等且互不依赖顺序；优先通过减少 sibling hooks 解决，不新建自研 dispatcher。

### 5.4 Gate 收敛

- hotfix2 先删 opt-in manifest/per-AC/TDD 子协议的死说明、保留 AC11/12 语义和错误解锁文案；不以更多 adapter 文件掩盖复杂度。
- 最小 ship 证据：可解析 AC、真实测试/运行证据、最新独立 review PASS、无 design drift、writer lifecycle/worktree 合法；R/S 再加 runtime、cleanup、architecture。
- 本轮不强制把巨型 gate 拆成多文件。先删除死分支和重复合同；若删减后仍难以测试，再在后续版本按 `spec / ship` 两个真实事件边界拆分。
- Codex 补齐未消解 `GateEscalated` 的 SessionStart 告警，与 Claude 语义对齐；告警不是放行。

## 6. 实施切片

1. **P0 正确性与安全**：修 read-only 误判、fresh CX 配置回归、manifest 真相漂移、命令日志泄露。
2. **控制面减负**：裁 token/tool trace/snapshot/continuator/no-op wiring，收窄 binding 和 `next_action`。
3. **双端 A/B 与发布**：同一 fixture corpus 验语义，再做 Quick/Feature/System dogfood；不按源码字节对称。

## 7. File Structure Plan

- 双端根 prompt、`athena-dev`、`pace`、`stages`、`orchestration`、design template：删除重复/错误合同。
- 双端 hook registry 与 `pace-continuator`、token/evidence/index/compact/subagent/worktree hooks：删空跑与 raw telemetry。
- 双端 delivery gate：删除 opt-in 子协议残留与错误文案，保留核心谓词。
- Codex `config.toml`、setup renderer、validator：修 fresh config 与模型默认漂移。
- validator/eval fixtures：增加 writer/read-only、normal Stop、tracked-state bytes、secret redaction 和双端 gate parity。

## 8. 验收标准

- [ ] AC1: 当前基线 2 个 validator FAIL 修复，完整 validator 与既有 gate fixtures 0 FAIL；fresh CX 不含空 `openai_base_url`，不手填 context/compact 模型元数据。
- [ ] AC2: read-only architect/critic/reviewer/spec/explorer 不需要 worktree、不写 lifecycle/violation；未隔离 writer 在 System 路径仍 fail-closed。
- [ ] AC3: 普通 prompt/Bash/Edit/MCP/SubagentStop/Stop 不生成 `token-usage.yaml`、`tool-trace.jsonl`、`subagent-log.md` 或 pre-compact snapshot；validation command 仍生成脱敏 PASS/FAIL evidence。
- [ ] AC4: 正常 Stop 不产生 Athena continuation prompt；只有 delivery gate 的真实未满足条件可以继续/阻断，且三次同因熔断后明确交还用户而不伪报 PASS。
- [ ] AC5: gate、stages 和 template 对 manifest 只有一个真相；默认流程不存在 review-manifest/per-AC 十字段/保留 AC11/12 义务及相关错误解锁文案。
- [ ] AC6: `next_action` 仅接受既有机器枚举，正常进度为空；breadcrumb 在最长合法信号下仍完整显示 stage 义务，且 ≤240 B；re-route 不因普通进度文本失效。
- [ ] AC7: read-only/诊断请求零 `.ai_state` 写入；Quick 首次实现写入前不强制 roadmap/design 文档；roadmap fixture 只对独立可 ship 切片触发。
- [ ] AC8: 双端同一行为 fixture 对 spec、review PASS、runtime、cleanup、architecture、roadmap、writer lifecycle/worktree 给出等强结果；不依赖 hook 声明顺序。
- [ ] AC9: 三类同任务 A/B 各 N≥3；质量 gate 不退化，正常模型回合数下降、p50 墙钟时间下降，自动版本化状态字节下降至少 80%，三项均须报告原始样本而非主观评价。
- [ ] AC10: 一个实现 slice 不产生 stage-only/progress-only commit；代码与最终状态按逻辑交付合并，ship 前最多一次集中状态同步，真实 blocker/用户决策/handoff 例外须说明原因。

## Scope lock — 本 sprint 与后续裁决边界

- 本 sprint 交付控制面收缩、双端安装同步与 git 单源度量仪器；`athena-metrics.py` 的 `verdict_ac2` 是本轮度量代理输出，不替代 AC2 的只读/worktree 行为判据。
- AC9 的三类 A/B、每类 N≥3、质量/回合/p50/状态字节原始样本是下一 sprint 的独立 gate；本 sprint 只记录基线，**不宣称 AC9 PASS**。
- 10.0 是否继续架构收缩，以下一 sprint 的 AC9 原始数据决定；本轮不因“原本纠结和啰嗦”追加新的控制面机制。

## 9. 非目标与风险

- 不删除 PACE 或 `.ai_state`，不新增 stage、第二状态树、runtime shared renderer 或 telemetry 配置开关。
- 不在本 sprint 更换模型、重写 setup/migrate、合并 26 skills，或直接修改安装态 `~/.claude` / `~/.codex`。
- 移除 raw telemetry 会降低事后取证粒度；release eval 显式采集和最终 review 证据承担替代，不让日常任务永久纳税。
- 减少文档合同不能削弱安全边界；所有删项都必须先证明无核心消费者，且变异测试能抓到真实违规。

## 10. 官方合同

- Codex hooks：同事件匹配命令并发运行，多个 context 会累加；Stop 只有明确 continuation 决策才应驱动新回合。https://learn.chatgpt.com/docs/hooks
- Codex Skills/AGENTS：Skills 渐进披露，AGENTS 应短且持久。https://learn.chatgpt.com/docs/build-skills · https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Codex config：`model_auto_compact_token_limit` 未设置时使用模型默认。https://developers.openai.com/codex/config-reference
- Claude hooks：匹配 handlers 并行；Stop、SubagentStop 是可续跑边界。https://code.claude.com/docs/en/hooks
- Claude memory/skills：CLAUDE.md 全量加载，skill 正文按需；项目存在共同 AGENTS.md 时可用 `@AGENTS.md`，但独立发行端点不得因此引入运行时跨包依赖。https://code.claude.com/docs/en/memory · https://code.claude.com/docs/en/skills

## Round 1 · Main Proposal

决策倾向：hotfix2 先做删除式重构，不新增机制。优先顺序为 P0 真相/安全 → 去自动账与续跑 → 收窄状态/编排 → A/B；任何“为了简化而新增的抽象”必须证明有至少两个真实消费者。


## Round 2 · Critic Findings (Fable 5, 2026-07-29)

### VERDICT: PASS (F1-F8 修订并入后实现)

先认账: 本稿修正了 Fable 前序工作的两处真实错误 (tool-trace 占比口径的仪器偏差 — 漏计 subagent worktree 代码; W18 re-route 被自由文本 next_action 永久关闭), 并收掉三处遗留 (模板契约漂移 / gate 误导文案 / snapshot 无消费者)。

### Findings 与处置 (全部已实现)

| # | Finding | 处置 |
|---|---|---|
| F1 | re-route 改 git 变更集但宿主未指定 | 宿主 = index-updater (原事件位), 数据源换 git diff/cached/untracked 三探针, 非 git 环境 fail-open 不触发 (W36) |
| F2 | 删 trace 前度量仪器真空 | `vibeCoding/scripts/athena-metrics.py` 先落地 (git 单源: code_diff/手写md/state 行数 + AC2 判定), 后删 trace (W35) |
| F3 | evidence.yaml 的 command 同样裸写 | 双端 redact(command) 覆盖 provider key、Bearer、assignment、CLI flag 与 URL userinfo; 冒烟覆盖上述形状 0 泄露 (W35) |
| F4 | 删 token collector 与 W21/W33 台账冲突 | 台账 W35 显式记 supersession, 防复核命令误报"被覆盖" |
| F5 | AC9 与被砍的 F6-A/B 需区分 | 区分依据: 本版指标全为低方差客观量 (回合数/p50/状态字节) 且三任务类分层, 非 prompt 质量主观 Pareto — C2 反对理由不适用 |
| F6 | 两条官方合同未验证 | 已 fetch: **CX Stop 仅 additionalContext 不续轮 (需显式 decision:block, 官方原文)** → continuator 双端删除安全; config 默认值文档截断, 保持待验证 (validator 兜底) |
| F7 | AC10 集中同步 × push 门禁交互 | stages 已有 ATHENA_ALLOW_PUSH 记账推送兜底通道, 引用即可, 未新增机制 |
| F8 | (新增) CX evidence result "fail (exit N)" 会让双端 validateEvidence 抛 unsupported → 一条失败验证永久卡死解析 | result 归一为 pass/fail/unknown; 冒烟实证 (W35) |

### 实现落点 (2026-07-29, 台账 W35-W40)

P0: 双端脱敏+trace 停产 (W35) · CX 只读角色豁免 (P0-1) · config.toml 三行清理 (P0-2, validator 2 FAIL 应转绿) · gate 文案+模板 annex 契约修 (P0-3)。
减负: 布线 (Stop 只留 gate / SubagentStop 去 token / PreCompact 删除 / CX index-updater 移出 UserPromptSubmit+Bash 组) · re-route→git (W36) · breadcrumb 去 next_action + 240B (W37) · next_action 枚举告警+模板注释 · AC11/12 特例与 meta-acceptance 删除 (W38) · CX SessionStart 熔断告警移植 (W39, 冒烟实证) · binding 只绑 writer (W40) · roadmap 地板 "≥2 独立切片" 六处改写 · .gitignore 遥测退出。
验证: node --check ×5 / py_compile ×6 全过; 行为冒烟 8 项全过 (脱敏×2 / trace 零生成×2 / re-route git 口径触发 / 散文告警 / R/S 无 manifest ship 双端放行 / CX 熔断告警注入)。validator 全量跑留待设备真仓 (本容器为局部镜像)。
