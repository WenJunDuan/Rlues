# Critique R2 · Athena 10.x（R1 候选全集 + 反驳）

> 调研日期 2026-09-24。来源标注：[官方] changelog/文档 · [源码] npm 包 · [本地] Rlues 实测 · [社区] 博客。
> 判定：MUST / SHOULD / COULD / 砍 / 待验证。每条至少挂 1 个反驳。

## 0. 调研基线（R1 输入）

| 平台 | 本地记录 (_index) | 最新 | 差距 | 来源 |
|---|---|---|---|---|
| Claude Code | 2.1.236 | **2.1.281** (npm 2026-09-23) | 45 个 patch | [源码] npm view |
| Codex CLI | 0.153.4 | **0.156.1** (2026-09-23) | 3 个 minor | [官方] learn.chatgpt.com/docs/changelog |
| Pi | 插件 peer `*` | **0.87.1** (2026-09-22)，包名已迁 `@earendil-works/pi-coding-agent` | 0.86/0.87 连续 breaking | [源码] npm CHANGELOG |

关键平台变化（与 9.9.9 描述冲突或可直接利用）：

| # | 变化 | 对 Athena 的影响 | 来源 |
|---|---|---|---|
| F1 | CC 2.1.269/2.1.274 多条 `/goal` 修复（重试、resume 保留、compact） | 9.9.9 宪法「CC 无原生 `/goal`」已过期 → hotfix | [官方] CC CHANGELOG |
| F2 | CC 2.1.277：项目无 CLAUDE.md 时读 AGENTS.md | 三端共用一份宪法正文可行（用户级 `~/.claude` 是否同样生效 **待验证**） | [官方] |
| F3 | CC 2.1.269：agent frontmatter `omitClaudeMd` | reviewer/generator 可不背宪法，省 token、少冲突 | [官方] |
| F4 | CC 2.1.271：subagent 结果带「subagent output」头 | 主 agent 可区分转述与一手事实（呼应提案 #16 转录断言） | [官方] |
| F5 | CC 2.1.269：`claude plugin eval` | Athena 若以插件分发，可直接挂行为评测 | [官方] |
| F6 | Codex 0.156.0：worktree 默认开启、thread 级 instructions provider、启动工具白名单 | CX 红区隔离不再需要手工 `git worktree add` 全流程（**待本机验证**） | [官方] |
| F7 | Pi 0.87.0：`turn_end` / `agent_before_settle` 可返回 `continue:true`；`shouldStopAfterTurn` 删除；`context_with_system` | Pi 端「Stop 无硬停，ship 只能 followUp」已过期 → 可做 ship 硬门 | [源码] |
| F8 | Pi 0.86.0：`user_bash` fail-closed；before_agent_start 变更跨 resume 持久 | athena-lifecycle.ts 每轮追加 IRON.md 的做法可改为一次性注入 | [源码] |

模型/社区共识（提示词方向输入）：

| # | 观点 | 来源 |
|---|---|---|
| M1 | Opus 5.5 medium ≥ Opus 5 high；**删「think carefully」/强制写推理**；控思考用 effort 不用提示词 | [官方] platform.claude.com prompting-claude-opus-5-5 |
| M2 | 无人值守循环别把「纯文本回合」当完成；用待办清单驱动续跑 | [官方] 同上 |
| M3 | 指令改「情境化」而非「普适化」（不要"每次编辑前读 A/B/C"）；删冗余的"记得测试"；skill 根文件做路由 | [官方] developers.openai.com GPT-6 Astra |
| M4 | 定义清楚"完成"比堆流程更防过早停 | [官方] 同上 |
| M5 | CLAUDE.md <60 行；**成功静默、失败才详细**；sub-agent 是上下文防火墙 | [社区] HumanLayer 2026-03 |
| M6 | Kirby 效应：新模型吸收旧 workaround，harness 每次换模型要做删除审 | [社区] Hugo Bowne-Anderson 2026-07 |
| M7 | guides(前馈) vs sensors(反馈)；计算型控制(确定、快) vs 推断型控制(语义、贵) | [社区] martinfowler.com 2026-04 |

本地实测（膨胀证据）：

| 指标 | 值 | 来源 |
|---|---|---|
| 宪法 | CC 4,049 B / CX 4,376 B；铁律 1 单行 ≈400 字 | [本地] |
| skills | 两端各 28；CC↔CX skills 差异文件 51 个 | [本地] diff -rq |
| Markdown 总量 | CC 283 KB / CX 317 KB | [本地] |
| 门禁实现 | delivery-gate cjs 1,612 行 + py 2,076 行 + **Pi fork 1,454 行（已与 CC 分叉）** | [本地] |
| `.ai_state` 记账提交 | 9 月 118 commit 中 73 个动 `.ai_state`（62%） | [本地] git log |
| `.runtime` | 35 MB，其中 3 个 q12 输入包各 12 MB | [本地] du |
| `_index.md` | 60+ 字段；「当前状态」段 5 行重复死锚 `#st-0` | [本地] |
| README 当前状态 | 停在 2026-08-27 / 9.9.8 | [本地] |
| 下版提案池 | next-version/proposals.md 累计 ≈51 条 | [本地] |

---

## R1 候选（放开写）→ R2 反驳

| # | R1 提案 | 反驳角度 | 反例/数据 | 判定 |
|---|---|---|---|---|
| A1 | **单源构建**：`athena/core + adapters/{cc,cx,pi}` → build 生成三端发行 | 维护成本：多一个 build 工具 | 反证更强：51 个 skill 差异文件、compound `cross-port-divergence-needs-cmp`、Pi 第三份 fork 已分叉。build 只做拷贝+变量替换，≤200 行 | **MUST** |
| A2 | **单一门禁核**（JS），CC/Pi 直接 require，CX hooks.json 改调 `node` | 跨平台一致性：CX payload 字段不同；删 py 丢什么？ | CX hook 是任意命令，node 本机已装（CC 依赖）。回滚=保留 9.9.9 py 发行。前置：共享 fixture 在三适配器全绿才切换 | **MUST**（风险最高项） |
| A3 | 三端都以插件/包分发（CC plugin / CX plugin / Pi package） | 来源可靠性 + 能力边界 | Pi 已是 package；CC 插件能否带 settings 权限、与用户 hook 的执行序 **未验证**；CX plugin 是否带 hooks **未验证** | **COULD**（只做 spike） |
| A4 | 三端宪法同一正文，build 生成 CLAUDE.md / AGENTS.md | 过度依赖 F2？ | 不依赖 F2：build 生成两份文件即可；F2 只是将来可再省一份 | **MUST** |
| A5 | **`.ai_state` v2 瘦身**（见 FINAL §4） | 跨项目 schema parity、已有项目迁移 | quantum-agent 已手工做过一次 tidy（68→11 sprints，handoff 339→queue 85 行），证明痛点真实且可迁移；需 migrate 脚本 | **MUST**（依赖 A2：门禁读字段） |
| A6 | **门禁分级**：可计算硬事实 block；语义/句式启发式降 advisory | 放松 = 漏拦？ | 近期误拦 #13 design_changed、#15 承诺句式、跨仓 push、#14 计数，全是启发式；每次靠人放行，消耗信任。保留 4 条硬门（见 FINAL） | **MUST** |
| A7 | 删 `harness-patches.md`，改为托管安装 + `doctor` 哈希比对 | 机械消费者 | gate `isLightShipFile` 按文件名消费；须与 A2 同刀删 | **SHOULD**（随 A1+A2） |
| A8 | `pace-continuator` 退役，改原生 `/goal` | 数据空白 | CC `/goal` 存在（F1）；CX `/goal` 本机未验；continuator 还承担 await-review 放行 | **待验证** → 评测证明等价才删 |
| A9 | reviewer/generator/polish 加 `omitClaudeMd: true` | 角色丢失风格约束 | 风格 1 行写进 agent 正文即可；reviewer 不需要路由规则 | **MUST**（CC）；CX/Pi 无等价，文档标注 |
| A10 | skills 28 → ≤18（合并 athena-status/checkpoint/preferences/setup/migrate；清 antigravity/augment/context7 包装） | 数据空白 | 无调用频次数据；仅 antigravity 有证据（`ag_callable: false`）。先跑 athena-metrics 统计 | **SHOULD**（先测再砍） |
| A11 | 行为评测集（brainstorm 已列 12 类）+ 门禁 fixture | 付费模型成本 | 门禁 fixture 纯静态零成本；行为评测只跑 3 个真实任务 | **MUST**（最小版） |
| A12 | 规则溯源 + 换模型删除审（Kirby） | 又一份文档 | 不新建文件：core 规则表加一列「补偿的失败 / 删除条件」 | **SHOULD** |
| A13 | Pi 0.87 `turn_end`/`agent_before_settle` 接 ship 硬门；peer 版本钉死 | API 抖动 | 3 天 2 次 breaking → peer `>=0.87 <0.88`，每升一版跑 fixture | **MUST** |
| A14 | 并行 subagent 注入时间预算信号 | 数据空白 | M1 仅官方建议，无本地数据 | **COULD** |
| A15 | 向量记忆 / 知识图谱 | 过度工程 | brainstorm 已暂缓，无新数据 | **砍** |
| A16 | 按模型分叉提示词（Opus/GPT-6/Grok 各一套） | 熵增 | 文件数 ×3；用 effort/设置解决 | **砍** |
| A17 | 51 条提案全量纳入 10.x | 把调研当合并（v9.7 反模式） | 门禁类多数被 A2/A6 吸收或作废；不该在即将被替换的双实现上修两遍 | **砍**（分流见 FINAL §2） |
| A18 | 用户级改用 `~/.claude/AGENTS.md` 取代 CLAUDE.md | 来源可靠性 | F2 只写「项目无 CLAUDE.md 时」 | **砍**（待官方明确） |

R1 18 项 → MUST 9（A1 A2 A4 A5 A6 A9 A11 A13 + 提示词重写）· SHOULD 3 · COULD 2 · 待验证 1 · 砍 4。
