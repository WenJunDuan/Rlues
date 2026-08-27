---
sprint_slug: "2026-08-27-athena-9-9-8"
path: "System"
created: "2026-08-27"
last_updated: "2026-08-27T18:55:00+08:00"
document_status: "revision2-post-independent-review"
implementation_authorized: true
authorization_note: "用户 2026-08-27 显式指令：设计修订后交 Grok 生成实现，Claude 按 packet 复盘"
baseline_release: "9.9.6-hotfix2"
target_release: "9.9.8"
roadmap_slug: "athena-9-9-8"
original_draft_author: "grok-4.6"
revision_author: "codex"
revision2_author: "claude-fable-5"
design_review: "reviews/design-review.md (2026-08-27, VERDICT: CONCERNS; F1–F7 已折入本版, F8 记为切片 3 可选项)"
author_does_not_review: true
---

# Design — Athena 9.9.8 Thin PACE Control Plane (rev2)

> Grok 草案 → Codex 修订 → 独立 Claude 挑战 (reviews/design-review.md, CONCERNS) → 本版折入全部 P1/P2 修正。设计挑战已完成一轮，不再重开；下一次 review 是**实现 review**，从同目录 `review-packet.md` (mode: implementation) 开始。实现者（Grok）不审自己的实现。

## 结论先行

PACE 与 `ai_state` 继续做 Athena 的内核；CC/CX 的 agent loop、上下文压缩、工具、权限、subagent 与 code review 交给官方 harness。9.9.8 不再用更多 prompt 和材料治理 prompt，而是删掉重复控制面：

1. 设计作者只交付 `design.md` 与机械派生的短 review packet，不运行 critic 循环。
2. 实现、运行验证、代码清理都结束后，只发起一次多维 code-review 请求；官方 harness 内部是否并行多个 reviewer 不计作 Athena 的多轮流程。**该请求是异步里程碑，不是同轮同步调用**（CC `/code-review` 自 2.1.221 起为后台 subagent，见「Review 异步时序」）。
3. 机械事实由 gate/test 直接验证；模型 review 只处理需要判断的 spec 偏差、正确性、安全、测试风险与过度工程。
4. `_index.md` 只保留有界活状态；历史 sprint 冷归档、telemetry 退出 Git、历史目录默认不进入上下文或递归检索。**迁移前先冻结 token baseline**（见「度量口径」）。
5. 模型与 effort 按任务风险路由，先用代表性 eval 再改 fresh-install 默认值；迁移绝不覆盖用户已有配置。
6. 所有版本敏感的承重断言钉 target 版本并双源；impl-entry 前重验（见「版本 pin」）。

目标是把"思考、审查、记账"占用从用户观察到的约 2/3 降到不高于 1/3，同时不降低交付门禁通过率。度量按「度量口径」节的定义执行，不凭观感验收。

## 官方证据与边界

### Anthropic

- [AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook)：核心可取之处是连续、已提交的产物链与风险门禁；下一阶段消费上一阶段的产物，而不是重演对话。文章原文说 deploy 前使用 **layers of agentic review**，并没有主张"单 reviewer"。9.9.8 的"一次 review 请求"是用户需求与 Athena 成本数据的本地决策，不冒充 Anthropic 结论。
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices)：上下文是有限资源；应删除模型本来就会做的 CLAUDE.md 指令，把确定性约束交给 hook，并用 subagent 隔离高噪声探索。
- [Claude Code review](https://code.claude.com/docs/en/code-review)：官方 review 本身可由多个专门 agent 并行查找、验证、去重和定级；`REVIEW.md` 是稳定的 review-only 规则，不应塞 sprint 叙事。
- [CC 官方 CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md)（一手源，rev2 新增）：**2.1.221 `/code-review` 改为后台 subagent；2.1.223 `/review` 成为其别名；2.1.233 todo/task 工具在 Opus 4.8/Sonnet 5/Fable 5+ 移除；2.1.232/2.1.218/2.1.217 subagent 默认 fork、默认不嵌套派发、并发默认上限 20；2.1.237 内置 Concise 输出风格；2.1.243 `/usage` per-loop 用量拆分**。
- [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)：优化对象是 system prompt、工具、MCP、历史与检索组成的整个上下文，而不只是根提示词长度。
- [Claude models](https://platform.claude.com/docs/en/about-claude/models/overview) 与 [effort](https://platform.claude.com/docs/en/build-with-claude/effort)：当前官方谱系以 Fable 5、Opus 5、Sonnet 5 与 Haiku 4.5 分别覆盖最强长任务、复杂 agentic、质量/成本平衡和快速任务；高 effort 会带来更多推理和工具调用，routine 工作应通过 eval 尝试 medium/low。

### OpenAI

- [GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model)：Sol/Terra/Luna 分别覆盖旗舰、均衡与高吞吐场景；官方建议瘦 prompt、每条指令只写一次、控制不断增长的上下文，并以代表性任务验证更低 effort。官方内部 coding-agent eval 的 token 降幅只能作方向证据，不能直接当 Athena 的验收结果。
- [Codex as a platform](https://developers.openai.com/blog/codex-as-a-platform)：Codex harness 已负责持久线程、保留 reasoning、compaction、工具、sandbox 与审批。Athena 不应重造 agent loop，只提供工作流契约与状态。
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[code review](https://learn.chatgpt.com/docs/code-review)、[hooks](https://learn.chatgpt.com/docs/hooks)：层级指令只放稳定规则；subagent 只用于独立/高噪声任务；`/review` 提供隔离的只读 reviewer；确定性生命周期规则交给 hooks。
- [Custom code review rules](https://developers.openai.com/blog/custom-code-review-rules-for-codex)：稳定 review 规则应短小且按目录作用域放置，避免每个 sprint 重复传入。
- CX 0.146–0.149 的新能力（`/export` 会话导出、`codex exec fork`、异步 hooks 调 MCP、agents dashboard）目前**仅二手源**（releasebot），github releases/tags 被 robots 拦截、API 受限，首屏一手确认止于 rust-v0.144.0 —— 全部标**待验证**，处理见「版本 pin」。

### 其他 harness 的共同方向

| Harness | 官方机制 | Athena 只吸收的方向 |
|---|---|---|
| [Cursor Rules](https://docs.cursor.com/context/rules-for-ai) | always/path/agent-requested/manual 规则 | 规则按路径和需要加载，不全局注入 |
| [OpenHands Skills](https://docs.openhands.dev/overview/skills) | 相关时按需加载 skill | skill catalog 只给短摘要，正文延迟读取 |
| [Gemini CLI memory](https://google-gemini.github.io/gemini-cli/docs/cli/gemini-md.html) / [checkpointing](https://google-gemini.github.io/gemini-cli/docs/cli/checkpointing.html) | 层级 context + harness 快照/恢复 | 运行态恢复优先用 harness，`ai_state` 只存跨会话事实 |
| [Aider repo map](https://aider.chat/docs/repomap.html) | 用紧凑符号图替代全库读取 | 历史检索先走小索引，不 glob 全树 |
| [Pi coding agent](https://github.com/badlogic/pi-mono) | 极小默认工具集，能力通过扩展加入 | 主循环保持薄，特殊能力显式启用 |

## 版本 pin 与承重断言重验（rev2 新增, F4）

本设计有三个版本敏感的承重断言。impl-entry 前由实现者机器重验；重验失败按黄区处理（warning + 记录 + 按实测能力面调整该项实现），不带病落地。

| # | 承重断言 | 一手源 | target pin | impl-entry 重验动作 |
|---|---|---|---|---|
| V1 | CC `/code-review` 为后台 subagent，`/review` 为别名 | CC CHANGELOG 2.1.221/2.1.223 | CC ≥ 2.1.246 | `claude --version`；实测发起一次 `/code-review` 观察是否后台返回 |
| V2 | CX 仅执行 command/MCP hook，`prompt`/`agent` handler 跳过 | codex 源码 dispatch（9.9.6 审查已核）| CX = 安装实测值（`codex --version`）| 0.146+ 若属实（异步 hooks 调 MCP），此断言可能已变 —— 按实测版本重读 hooks 文档与 `config.schema.json` |
| V3 | 同事件多 hook 并发启动、配置顺序非优先级 | CC/CX hooks 官方文档 + 9.9.6 现场观测 | 同上 | 双端各跑一个双 hook fixture 确认 |

约束：`_index.cc_version/cx_version` 在 impl-entry 时更新为实测值（当前记录 cc 2.1.211/cx 0.145.0 已过期）；设计中所有"CX 0.146+"特性（如 `/export` 作转录载体）在 V2 重验前只能作候选，不得作为唯一实现路径。

## 对 Grok 草案的修正

| 草案问题 | 9.9.8 修正 |
|---|---|
| 把 Anthropic 写成"一层 agent review" | 改为"一次 Athena review 请求"；允许官方 harness 内部多 agent 并行 |
| Feature+ 固定独立 design review | 移除固定税；只有 Refactor/System 或用户显式要求才独立挑战，本 sprint 属于后者 |
| 20KB design 再复制一份长 packet | packet 是有 hash 的派生投影，目标不超过 80 行，不是第二真相源 |
| canonical baseline 写成用户安装态 `luna/max` | 发行源基线是 CX `gpt-5.6-sol/high`；用户安装态单列，migration 保留覆盖值 |
| 要求 generator 与 polish 都去掉 `skills: [pace]` | rev2 更正（F5）：9.9.6 CC 实际命中三处 —— generator、critic、architect（grep 实证；polish-worker 未命中）。处置：generator 去掉；critic 随角色删除消失；**architect 保留 `skills: [pace]`**（独立挑战需要路由/路径全景，属真实消费，非重复注入）。CX 侧按同名 agent 文件逐项核对，不写虚假对称 AC |
| 新建手写 `_catalog.yaml` | 改为可重建、被忽略的 runtime cache；权威事实仍是 `_index`、文档 frontmatter 与 Git |
| review 后再 polish | 改为先完成会改代码的 polish，再 review 最终 diff；review 后只允许 ship housekeeping |
| gate 解析标题与 critic 次数 | 用单份结果 frontmatter + exact hash；不再数 Markdown 标题充当语义 |

## 目标流程

```text
request → route → design/packet → implementation → tests/runtime-verify
        → code-changing polish → one native review request (async)
        → [完成通知轮: 落盘/校验结果] → ship/state sync
```

若 review 发现必须修改代码，原结果因 diff hash 变化而失效，只对 open findings 与增量 diff 发起一次目标复核；不预排 pass2/pass3，也不重新运行固定三角色。**目标复核终止规则（F3）：同因 ×2 仍出新 P0 → 停止复核，交还用户裁决；禁止无界复核（那是 passN 换名复活）。**

### 按风险收费

| Path | 设计交付 | 独立设计挑战 | 最终 code review | 额外义务 |
|---|---|---|---|---|
| Hotfix | 可省略 | 否 | 风险触发 | 可运行测试 + fix note |
| Quick | 简短 plan/AC | 否 | 用户或风险触发 | 绿区直接做 |
| Bugfix | issue 三件套即契约 | 否 | 一次 | 复现 + 回归测试 |
| Feature | design + packet | 默认否 | 一次 | TDD |
| Refactor/System | design + packet | 一次独立挑战 | 一次 | worktree、runtime-verify、pre-review polish、architecture |

设计作者永不审自己的设计。这里的"默认否"不是允许自审，而是根本不创建 design-review 这一步。

## Review contract

### 单一来源与派生 packet

- `design.md` 保存 WHY、决策、风险、文件结构和带 ID 的 AC，是设计真相。
- `review-packet.md` 由模板/脚本从 design 的 AC、风险和 scope 生成，含 `source_design_sha256` 与完整 AC ID 集；允许补充本次 reviewer 指令，不允许手工改变契约。
- impl-entry gate 机械校验 design hash、AC 集合双射和 packet 行数；不把"packet 是否完整"再交给模型判断。
- generator 读 packet 与指定文件；reviewer 读 packet、diff、短 evidence summary 与稳定 standards。只有出现矛盾时才按 packet 的 section anchor 定点打开 design。

### 一次多维 review

Athena 发出一次 review 请求，使用当前 harness 的原生能力：

| 端 | 首选入口 | Athena 提供 |
|---|---|---|
| CC | `/code-review`（2.1.223 起 `/review` 为其别名）| 稳定 `REVIEW.md` + sprint packet + diff/evidence |
| CX | `/review` 的 dedicated reviewer | scoped `AGENTS.md` review rules + sprint packet + diff/evidence |
| 无原生入口 | 单个只读 reviewer agent | 相同输入/输出 schema |

固定维度：Spec coverage、Correctness、Security、Test risk、Over-engineering；Refactor/System 再核 Evidence。测试是否执行、文件是否越界、runtime evidence 是否存在由 gate 直接判，reviewer 不重复跑一遍账本审计。

单份 `reviews/implementation-review.md` 用 YAML frontmatter 提供机器字段：

```yaml
schema_version: 1
mode: implementation
packet_sha256: "..."
reviewed_diff_sha256: "..."
review_run_id: "..."
native_output_ref: "..."   # rev2 新增: 原生 review 原始输出引用 (transcript/export 路径); fallback agent 直写时为 "direct"
verdict: PASS
finding_counts: {P0: 0, P1: 0, P2: 0}
dimensions: [spec, correctness, security, tests, overengineering, evidence]
```

Markdown 只写 findings 与必要证据。Gate 校验字段、hash 和阈值；不要求 `## Spec Compliance`、`Critic Findings`、passN 数量或 evaluator 的第二次转述。

### Review 异步时序（rev2 新增, F1）

CC `/code-review` 自 2.1.221 起是**后台 subagent**：结果以完成通知在后续 turn 到达。9.9.6 review 报告 P0-2 已证明"同轮收齐后台结果"架构上不可能。因此：

- 发起 review 请求后，当前 turn **正常结束**；主 agent 设 `_index.next_action = "await-review-result"`。
- Stop hook / pace-continuator 对 pending review **放行**，不 block、不注入续跑提示（等待不烧 token）。
- 完成通知轮：主 agent 校验结果、按「结果落盘规则」写入/确认 `reviews/implementation-review.md`，恢复 `next_action`。
- ship gate 只认"结果文件存在 + packet_sha256/reviewed_diff_sha256 与现场重算一致"，**不认时序**，也不假设 review 与实现在同一会话。
- 双端 fixture 必须含"后台完成通知轮"用例（发起→结束→通知→落盘→gate 通过）与"通知丢失"用例（结果文件缺失时 ship gate block，提示重新发起而非伪造）。

### 结果落盘规则（rev2 新增, F3）

原生入口在会话流里输出 findings，不会自己写带 frontmatter 的结果文件。为了不复活"主 agent 伪造 findings"暴露面：

1. **fallback reviewer agent 路径**：结果文件由 reviewer 会话直接写，`native_output_ref: "direct"`。
2. **原生入口路径**：主 agent 可转录，但 `native_output_ref` 必须指向原生 review 原始输出的可核引用（CC transcript 路径；CX 侧候选 `/export` 产物 —— V2 重验前不得作为唯一实现），该引用作为 evidence 落盘。
3. gate 校验 `review_run_id` 存在且 `native_output_ref` 指向的文件/路径存在；两者缺一 → ship block。
4. 转录只许照抄 findings 与 verdict，不许增删定级；抽查手段是 diff 转录稿与 `native_output_ref`。

## PACE 与 harness 的职责边界

| PACE/ai_state 保留 | 交还官方 harness | 删除的重复控制面 |
|---|---|---|
| route、AC、风险分级、跨会话状态、delivery gate | agent loop、context compaction、工具权限、原生 subagent/review | critic 固定轮次、2+1 review 编排、重复 evidence 解读、只读 agent 手工绑定账本 |

- 根 `CLAUDE.md`/`AGENTS.md` 只放始终成立的宪法与授权边界；阶段细节只在相关 skill 加载。
- read-only architect/reviewer 直接用 harness task identity，不做手工 assignment handshake；只有会写文件且 ship gate 依赖其身份的 worker 保留绑定。
- skill 名保持，不为 9.9.8 合并 26 个 skill；但 catalog description 压到触发条件一行，正文按需读取。
- CC/CX 只对齐语义，不伪造相同命令、模型名或内部多 agent 拓扑。
- rev2（F7）：**"tasks 全绿 (Sisyphus)"类话术统一改指 `checklist.yaml` 自有文件** —— CC 2.1.233 起 todo/task 工具在 Opus 4.8/Sonnet 5/Fable 5+ 已移除，凡可能被读成依赖 CC 原生 task 工具的表述都在切片 2 扫描面内。
- rev2（F8）：orchestration.md 的编排假设同步 CC 现实 —— subagent 默认 fork（2.1.232）、默认不嵌套派发（2.1.218）、并发默认上限 20（2.1.217）。

## Hook 严格度：只有边界可以 block

结论是**当前局部过严**，不是应该把 hook 全部关掉。现场已有三类证据：无害 `rg` 正则因单引号内的转义括号被 `pre-bash-guard` 误报为不可解析 command substitution；repo 外 harness 写入被 worktree hook 两次结构性死锁；delivery gate 仍包含 critic 标题计数、可选 manifest 等历史协议。Codex 当前每次 patch 同步启动 1 个 pre-gate，随后再启动 evidence/design/index 三个进程；官方说明同事件匹配 hook 会并发启动，配置顺序不是优先级。

| 区域 | 处理 | 例子 |
|---|---|---|
| 红：安全、不可逆、最终交付真值 | fail-closed block | 根目录递归删除、裸设备写、network-to-shell、越权外部写、非 ship push、测试失败、review 与最终 diff hash 不符 |
| 黄：可修复的流程/质量信号 | warning + 一条解锁动作 | VM 未覆盖、design 超预算、可选 artifact 缺失、历史索引陈旧、parser 对已证明只读 AST 不确定、版本 pin 重验失败 |
| 绿：记账与提示 | async / fail-open / 不注入模型上下文 | telemetry、breadcrumb、index refresh、notification、可重建 catalog |

收敛规则：

- `PreToolUse` 只阻断"当前动作一旦执行就越过信任边界"的红项；impl-entry spec gate 只在首次源码写入核 packet，任何 `.ai_state` 修复写必须可执行。
- shell parser 必须理解引号与转义。解析失败时，明确的 mutating/unknown 命令继续 fail-closed；只有通过窄 read-only AST 白名单的命令 warning 后放行，并为本次 `rg` 误判加入双端 fixture。
- 同一事件最多一个同步 blocker；PostToolUse 的证据/索引/遥测要么合并必要工作，要么后台运行，失败不得制造模型续跑。
- `Stop` 只校验当前 stage 真正到期的义务；失败返回一个当前角色能完成的动作，同因三次后交还用户，不用 continuation 制造活锁。**pending review（await-review-result）视为义务已尽，放行**（见「Review 异步时序」）。
- 不把 LLM judge/verifier 放进同步 hook。当前 Codex 官方只执行 command/MCP hook，`prompt`/`agent` handler 会被跳过（V2，impl-entry 重验）；语义验证应是显式 review/eval 调用。

## `ai_state`：热状态、耐久知识、冷历史

| 层 | 内容 | 默认读取 |
|---|---|---|
| 热状态 | `_index.md` + 当前 sprint | 每轮只读 `_index`，再跟当前 pointer |
| 耐久知识 | `requirements/`、`architecture/`、`compound/` | 只有当前任务命中时读取 |
| 冷历史 | `sprints/archive/YYYY/{slug}` | 默认排除；按 slug/关键词显式查询 |
| 运行 telemetry | `.ai_state/.runtime/` 或 `~/.athena/runs/{repo-id}` | Git ignored，保留最近 20 次或 14 天 |

约束：

- `_index.md` 不超过 12 KiB，任何 history/log 列表最多 10 项；**rev2（F6）：另加单条上限 —— 每条 ≤160 字节；溢出不静默丢弃，由 hook 把全文搬入 `sprints/{slug}/route-note.md`（或对应 sprint 文档），`_index` 留一行摘要 + 指针**。现 `_index` 13.8KB 超标的主因就是 route_history 单条 200–600 字散文，条数早已合规 —— 治单条长度，不是治条数。审计链不许被截断销毁（铁律[证据与出处]）。
- ship 先把仍为真的需求、架构、经验做一次 delta merge，再把已关闭 sprint 移入 archive。
- `.ai_state/.runtime/catalog.jsonl` 可从 frontmatter 重建，只是检索 cache，不是第二真相源；SessionStart 和 index-updater 永不递归 archive。
- `_index` 可以保留一个直达 archive 的"latest artifact"指针，但不会自动展开内容。
- 当前已跟踪的 `token-usage.yaml`/`tool-trace.jsonl` 迁移时保留本地副本，再从 Git index 移除；不删除用户数据。**rev2（F2）：迁移与 retention 生效前，必须先完成「度量口径」节的 baseline 冻结 —— 顺序颠倒 = AC11 失去对照组，gate fixture 对此断言。**
- rev2（F8, 可选项，不阻塞 9.9.8）：CC `/usage` 已有 per-loop 用量拆分（2.1.243）、原生 OTEL 遥测可用 —— 切片 3 可评估把 token-usage-collector/tool-trace 自建采集降级为"仅补 harness 不给的字段"，进一步削 PostToolUse 记账面。评估结论记 compound decision，不强制本版落地。

当前仓库约 3.6 MiB、243 个文件、22 个 sprint；字节主要由 telemetry 占据（前四大文件均为 token-usage/tool-trace，最大单文件 796KB），查找税则来自平铺历史与无界 `_index`。因此先做有界索引与检索协议，不引入 SQLite/embedding；只有实际测量仍慢时再升级。

## 度量口径（rev2 新增, F2）

AC11 的"控制面 token"按以下机械口径归类，不凭观感：

- **控制面 token** = 以下三类会话/turn 的输出 token 之和：
  1. 产物落在 `.ai_state` 记账/review/route 类文件（session-log、route-note、reviews/*、evidence 解读散文）的 turn；
  2. review/critic/evaluator/spec-compliance 类 subagent 会话全量；
  3. hook 注入 continuation/提醒文本引发的额外 turn。
- **非控制面** = 产出代码/测试/可运行配置的 turn、runtime-verify 实跑、用户对话本身。
- 归类依据 token-usage.yaml 的 per-turn 标签（agent role + 落盘目标路径）；标签不足以归类的 turn 计入控制面（从严，防止口径注水）。

**baseline 冻结（先于切片 3 执行）**：从 9.9.6 代表性 sprint（至少覆盖 Quick/Bugfix/Feature/System 各一）导出 per-turn 用量为 `baseline-9.9.6-tokens.json`，存 `.ai_state/.runtime/baseline/`（ignored 但**显式豁免 retention**）。AC11 的 ≥40% 下降与 ≤1/3 占比均对照该冻结文件计算。

## 模型与 effort 策略

推荐路由，不在本 sprint 未经 eval 写死全局值：

| 工作 | CC 候选 | CX 候选 | effort 起点 |
|---|---|---|---|
| 机械读取/检索/格式化 | Haiku 4.5 | Luna | low |
| 常规实现与主循环 | Sonnet 5 | Terra | medium |
| System 设计/复杂调试 | Fable 5 或 Opus 5 | Sol | high；必要时 xhigh |
| 最终独立 review | 与作者不同家族优先 | 与作者不同家族优先 | high |

实施前用 9.9.6 的代表性历史任务做同 effort 与低一档对照，至少覆盖 Quick、Bugfix、Feature、System；记录成功率、gate、有效 findings、tokens、耗时。只有质量非劣且控制面 token 明显下降才改 fresh-install 默认。用户安装态设置永不被 migrate 覆盖。安装态可默认启用 CC "Concise" 输出风格（2.1.237，零成本省 token；用户已设 output style 时不覆盖）。

## 实现切片与文件面

### 1. review-contract-and-flow

- 双端根 prompt、`pace/references/stages.md`、`athena-review/SKILL.md`：删 critic 下限与默认 2+1，改成一次原生 review 请求。
- **异步时序落地（F1）**：`_index.next_action=await-review-result` 语义；Stop/pace-continuator 放行 pending review；完成通知轮工作流写入 stages.md；双端"后台完成通知轮"与"通知丢失"fixture。
- **结果落盘规则（F3）**：`native_output_ref` 字段 + gate 校验；目标复核同因 ×2 终止条款写入 stages.md 与 gate。
- reviewer/result/packet 模板：加入 hash、AC 集和统一 frontmatter；旧 critic/evaluator/spec-compliance 留兼容 stub，禁止 live emitter 调度。
- delivery/spec gate：按结构化字段和 exact diff 校验；删标题计数，并按红/黄/绿重分 block 条件。
- R/S 顺序改为 runtime-verify → code-changing polish → review → ship。

### 2. harness-context-and-model-policy

- CC/CX reviewer、generator、SessionStart、continuator、index renderer 全量扫描旧话术；**扫描面含"tasks 全绿"类表述改指 checklist.yaml（F7）**。
- pace 预加载按实况处置（F5）：CC generator 去掉；critic 随删除消失；architect 保留（写明理由）；CX 按同名文件逐项核对。
- read-only agent 取消手工 binding。
- hook registry 保证同一事件最多一个同步 blocker；PostToolUse 记账不触发模型续跑；增加 quote-aware/read-only parser 回归夹具。
- **impl-entry 版本 pin 重验（F4）**：V1–V3 三断言按「版本 pin」表执行并更新 `_index.cc_version/cx_version`。
- orchestration.md 同步 CC 并发/嵌套/fork 现实（F8）。
- 加 token/eval 采样，验证后再调整 fresh-install model/effort；migration 保留用户值。

### 3. state-retention-and-retrieval

- **先冻结 baseline（F2，本切片第一步，gate fixture 断言顺序）**。
- `_index` 模板/更新 hook 加 12 KiB 总量、列表 ≤10 项、**单条 ≤160B + 溢出搬运**（F6）。
- archive 默认排除，生成可重建 runtime catalog；telemetry 迁到 ignored runtime 目录并设 retention（baseline 目录豁免）。
- ship 时只做一次 durable delta merge 与 archive。
- 可选：自建 telemetry 采集降级评估（F8），结论记 compound decision。

## 验收标准

- **AC1**：任何作者会话都不 spawn critic；Feature 也不默认生成 design-review；R/S 或用户显式要求的独立挑战从派生 packet 开始。
- **AC2**：packet 含 design hash 与完整 AC ID，最多 80 行；fixture 对陈旧 hash、漏/重 AC 必须 fail closed。
- **AC3**：实现完成后的默认 Athena 调度只有一次 review 请求和一份 result；live emitter 不再调度 spec-compliance/evaluator/固定 pass2/pass3。**review 请求为异步里程碑：发起轮正常结束，Stop/continuator 对 await-review-result 放行不注入续跑；完成通知轮落盘。**
- **AC4**：原生 harness 内部可多 agent；Athena 不重复编排。代码变更使旧 review 的 exact diff hash 失效，只做目标复核；**目标复核同因 ×2 仍出新 P0 → 交还用户，禁止无界复核。**
- **AC5**：R/S 的最终 review 位于所有会改代码的 polish 之后；review 后若代码变化，ship gate 必须 block。
- **AC6**：review result 用结构化 frontmatter；gate 不再依赖 `Critic Findings`、`## Spec Compliance` 或 passN 标题数量。**result 须含 `review_run_id` 与 `native_output_ref`（原生输出可核引用或 "direct"），任一缺失 → ship block；转录不得增删定级。**
- **AC7**：Quick/Hotfix/Bugfix/Feature/R/S 的仪式与表一致；hook 只对红区 fail-closed，黄区不阻断、绿区不续跑；测试、安全、权限和 worktree 真边界不降级。
- **AC8**：双端只对齐语义；同事件最多一个同步 blocker；read-only role 无手工 assignment，writer 绑定仍可核验；无害 `rg` quote/regex fixture 通过，旧 2+1 话术不出现在 live emitter；**"tasks 全绿"类表述全部改指 checklist.yaml。**
- **AC9**：`_index` ≤12 KiB 且列表 ≤10 项、**单条 ≤160 字节，溢出由 hook 搬运至 sprint 文档而非丢弃**；archive 不被默认扫描；runtime catalog 删除后可重建；telemetry 不再由 Git 跟踪。
- **AC10**：canonical 9.9.6 基线、用户安装态与 9.9.8 target 分开记录；migration 保留用户 model/effort，默认降档必须通过代表性 eval。
- **AC11**：双端 validator 与 runtime fixture 0 FAIL；对比**冻结 baseline**（`baseline-9.9.6-tokens.json`，按「度量口径」归类）时，交付成功率/安全门禁不降低，median 控制面 tokens 至少下降 40%，控制面占比不高于 1/3。
- **AC12**：不新增第二状态树、不合并 26 skill、不新增人工维护 catalog；派生 packet 最多 80 行且不复制 design 散文。
- **AC13**（rev2 新增）：impl-entry 完成 V1–V3 版本 pin 重验并更新 `_index.cc_version/cx_version`；重验失败的断言按黄区处理并按实测能力面调整实现，CX 0.146+ 特性在 V2 通过前不得作为唯一实现路径。

## 发布边界

三个切片各自可回滚，review-contract 先落；模型默认和 archive 迁移不与审查门禁绑成一次不可回滚改动。**切片 3 内部顺序不可回滚点：baseline 冻结先于 telemetry 迁移/retention 生效（F2）。**实施对象若含 repo 外安装态，按 harness 外部目标逐文件备份。设计挑战已完成（reviews/design-review.md）；`implementation_authorized: true`（用户 2026-08-27 指令）。实现 review 由非实现者会话按 `review-packet.md`（mode: implementation）执行。

## 未来接入槽（9.9.8 不实现）

这两条都可以在 9.9.8 之后打开，且**不需要改 PACE 路径名**。本 sprint 只保证不堵死接线、不把它们做成默认热路径。

### A. `athena-vm`：已经做成，缺的是注册而不是设计

自 9.9.0 起双端就有 `/athena-vm`（setup / doctor）。配置在 `~/.athena/vm.json`（chmod 600，**不进 git**），SSH 别名 `athena-vm-{name}`，`_index.tools_available.vm_available` 由 doctor 翻转。runtime-verify 的环境矩阵已经写了：`vm_available=true` 时 System/Refactor 加一轮远端实跑。

当前本机是关的：无 `~/.athena/vm.json`，`_index.vm_available: false`。未来可以直接启用：用户提供一台可 SSH 的 Linux VM，setup 写全局 0600 配置，doctor 核主机指纹/OS/磁盘并记录 `checked_at`，成功后才把 flag 置 true。不新写 skill，不进 9.9.8 切片；禁止明文密码，key 优先。

默认策略是 advisory：VM 不通必须在 `runtime-verify.md` 记"未覆盖"，但不能让所有 System 无条件停摆。只有当前 design 明确把某个 OS/native/破坏性场景列为 required 时，doctor 失败才 block。`vm_available` 表示最近一次 doctor 的带时效结果，不应被长期当静态配置。

以后可替换传输层，不替换契约：Codex Droplet Workspace / Claude Code remote 可以当另一种 runner，skill 仍只暴露「干净环境 + 破坏性隔离 + 命令与输出进 `runtime-verify.md`」。VM 永远是**确定性 verifier**（退出码、测试、HTTP 断言），不是模型打分。

### B. LLM-as-a-Verifier：可集成，但不能当发货门禁

来源：[arXiv 2607.05391](https://arxiv.org/abs/2607.05391)、[llm-as-a-verifier](https://github.com/llm-as-a-verifier/llm-as-a-verifier)、Claude/Codex 侧 [TurboAgent](https://github.com/llm-as-a-verifier/TurboAgent)。做法是细粒度分数（如 1–20）+ 对 score token 的 logprob 期望 + 重复抽样 / 标准分解，用来 **best-of-N 排序** 和进度估计，不是 PASS/FAIL 法律。它与普通 LLM-as-judge 不同；[OpenAI Graders](https://developers.openai.com/api/reference/resources/graders) 可作离散 rubric baseline，[Anthropic agent eval 指南](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) 也要求 deterministic-first、LLM grader 与人类校准。

硬边界：

1. **当前 Claude 不能直接充当"论文原义的概率 verifier"。** Anthropic 的 OpenAI SDK 兼容层明确忽略 `logprobs/top_logprobs`，TurboAgent 因而用带 logprobs 的 Gemini/DeepSeek/OpenAI-compatible 后端。Claude 仍可生成候选，也可做普通 rubric judge；不要把两种 verifier 混为一谈。
2. **默认打开会反着干 9.9.8。** N 路候选 + 锦标赛会把实现 token 乘上去；这是选优税，不是审查税。只允许在「测试已绿、仍有多个合格 diff」时 opt-in。
3. **评分标准必须等于 review-packet 的 Done checks**，禁止另造一套「感觉更好」。分数只排序，**不替代** test / delivery-gate / VM 实跑。gate 仍然 fail-closed。
4. **不要做成全局 `ANTHROPIC_BASE_URL` 代理。** 用户已有本地网关；TurboAgent 默认占 8888 会和第二代理叠层。以后若接，用显式 `athena-preferences` 开关和独立端口，fresh install 默认关。
5. **CX 自定义 gateway 若无 logprobs，这条整段 skip**，不得伪造离散 1–5 分冒充 LaaV。
6. **先校准再相信排名。** 用历史 PASS/FAIL 与人工 review 建小型 gold set，记录 pairwise accuracy、翻转率、成本和 verifier/author 同家族偏差；未达到预先写明的阈值前只记 telemetry。

推荐落点（9.9.9+ 或独立 opt-in）：runtime-verify / 多候选 generator 之后、一次 native review **之前**，写一行 `verifier_rank` 进 ignored runtime telemetry；reviewer 可以读排名，但不能把排名当 VERDICT。

不采用：用 LaaV 替换一轮 review；用 LaaV 替换 VM；为 LaaV 新建 PACE stage。
