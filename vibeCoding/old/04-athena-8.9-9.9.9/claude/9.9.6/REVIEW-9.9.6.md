# Athena 9.9.6 审查报告 · REWORK

审查范围: `vibeCoding/{claude,codex}/9.9.6` 全量提示词面 (宪法 / 26 skill / 7+9 agent / rules|standards / settings.json + config.toml + hooks.json / pace references)。
核验基准: 官方文档与源码 (code.claude.com/docs、learn.chatgpt.com/docs、openai/codex `config.schema.json`)。
方法: harness-iteration skill 的 S2 白名单 fetch 协议 + 八条铁律逐条自检。

---

## 0. VERDICT

**REWORK** — 3 个 P0。其中 2 个是"装上就炸"级别，静态验证器再跑 100 次也抓不到。

不是提示词写得差。9.9.6 的分层、铁律溯源、sprint contract、预算实测都在业界上沿。问题全部集中在**层间契约无机器断言**这一处，下面第 4 节展开。

---

## 1. P0 (阻断发布)

### P0-1 · CX `openai_base_url = ""` 会在第一次请求时炸

`config.toml` 第 9 行 `openai_base_url = ""`。

源码判据 (`codex-rs/model-provider-info/src/lib.rs`):
```rust
let base_url = self.base_url.clone().unwrap_or_else(|| default_base_url.to_string());
```
`unwrap_or_else` 只在 `None` 触发。TOML 空串反序列化为 `Some("")` → 官方默认 `https://api.openai.com/v1` **永不代入**。仓库全局 `base_url.is_empty` 命中 0 次，无空串守卫。

后果: 配置加载成功、启动无报错，**每一次模型请求失败**。

同时与自家契约文档直接矛盾 —— `codex/9.9.6/.codex/skills/pace/references/platform-contracts.md`:
> "The fresh template exposes `openai_base_url=https://api.openai.com/v1`"

**修**: 删掉这一行。不是置空，是删除。网关用户由 migration 写入实值。

---

### P0-2 · `background: true` 让 review 三件套的合并步骤在架构上不可能完成

`agents/reviewer.md` 与 `agents/spec-compliance.md` frontmatter 均为 `background: true`。

官方语义 (code.claude.com/docs/en/sub-agents，v2.1.211):
> "A background subagent's results reach Claude as a completion notification **in a later turn**."
> "Background subagents run with a **smaller built-in tool set**."

而 `athena-review/SKILL.md` 的工作流写的是:
> 1. 主 agent 并行运行 reviewer 与 spec-compliance
> 3. 主 agent **收齐结果**，串行写入 `reviews/passN.md`
> 4. 主 agent **再运行** evaluator

同轮收齐 + 同轮合并 + 同轮串起 evaluator —— 三步都要求前序结果在**当前 turn** 可用。`background: true` 明确排除这一点。

次生问题: reviewer 工作流第 2/3 步是 `git diff main...HEAD`，依赖 Bash。背景 subagent 的工具集被官方描述为"更小"，Bash 是否在内未证实 → 即使跨 turn 拿到结果，也可能是空 diff。

`references/stages.md` 给出的理由已过期:
> "后台 review agent 异步写产物, 同步等待会死锁"

但同一版本的 `athena-review/SKILL.md` 明写"两个 read-only agent **只返回完整 markdown 段, 不创建或修改文件**"。写产物的前提没了，死锁论证随之失效 —— 这是上一代设计残留的注释。

**修**: 两个 agent 删 `background: true`。同步删掉 stages.md 那条过期注释。
补充: v2.1.198 起 subagent **默认后台**，"Claude runs a subagent in the foreground when it needs the result before continuing" —— 删掉字段还不够，编排提示词里要明确写"需要本轮结果"。

---

### P0-3 · CX 红区"只能审计不能阻断"的前提已经不成立

`RELEASE.md` 已知风险 #2 与 `subagent-worktree-audit.py` 的整个设计基于一句判断:
> "Codex 0.145 的 multi_agents_v2 handler 不派发 `PreToolUse`，spawn 前阻断面在 Codex 上不存在"

官方与源码判据:
- learn.chatgpt.com/docs/hooks 工具覆盖表: "Other local function tools … **`spawn_agent` also matches `Agent`**" (PreToolUse: Yes / PostToolUse: Yes)
- `codex-rs/core/src/tools/registry.rs` 集中派发 `run_pre_tool_use_hooks`；`function_hook_tool_name` 对 `spawn_agent` 的 V1 命名空间形式与 V2 裸形式**都**做了特化
- 测试 `spawn_agent_function_tools_use_agent_matcher_alias` 断言两种形式均产出 payload
- issue #20204 (multi-agent handler 静默) 已被 **PR #23757 (2026-05 合入)** 取代

也就是说: 之前观察到的"不派发"是 matcher 命名问题，不是派发缺口，且已修。

后果: 双端最大的一处能力不对称 (CC 真阻断 / CX 事后审计 + 未接入 ship 门禁的孤儿 jsonl) **本来就不必存在**。CX 可以做和 CC 同级的 `PreToolUse` 真阻断。

**修**: CX `hooks.json` 加 `PreToolUse` matcher `spawn_agent|Agent` → 复用 CC `subagent-worktree-check` 逻辑。`subagent-worktree-audit.py` 降为事后兜底并接入 delivery-gate (原"剩余缺口"一并消掉)。
命名同步: 文件名 `audit` 是刻意选的诚实命名，改成真阻断后要改回 `check` —— 名字必须说实话，这条规矩两个方向都成立。

---

## 2. P1

| # | 问题 | 判据 | 修 |
|---|---|---|---|
| P1-4 | **CC `athena-runtime-verify/SKILL.md` 代码围栏不闭合** —— 全文 ` ``` ` 计数 = 1 (奇数)，第 29 行残留孤立围栏 + 断头行 `## VERDICT: PASS \| REWORK(回 impl)`。之后全部正文被吞进代码块 | 26 个 CC SKILL.md 中唯一一个奇数围栏；下沉 `references/playbook.md` 时截断 | 补/删围栏；validator 加"每个 SKILL.md fence 数为偶"断言 |
| P1-5 | **验证器自身回归** —— 9.9.3 有 12 个 `check_*` / 44 KB，9.9.6 只剩 10 个 / 21.8 KB。按名消失: `check_package_parity` (CC↔CX 对等，铁律[四原语])、`check_f_series_regressions` (历史 P0 回归)、`check_install_contract`、`check_runtime_contract`、`check_fresh_codex_runtime`。全文 grep `parity\|regress\|install\|rollback\|migrat` = 0 命中 | 9.9.6 validator 逐行读过 | 回填；且 ratchet 原则要落到 validator 自身: 断言只增不删 |
| P1-6 | **CX `hooks.md` ↔ `hooks.json` 双向漂移** —— 文档称 `subagent-retry.py` 挂 PostToolUse，hooks.json 里 grep = **0** (1,559 B 死文件)；反向，`subagent-worktree-audit.py` 实际注册在 SubagentStart，hooks.md 提及 = **0** (9.9.6 唯一新增安全 hook，读文档的 agent 看不到) | grep 计数 | 双向对齐；validator 加"注册集合 == 文档表格行集合" |
| ~~P1-7~~ | ~~`gpt-5.6-sol/terra` 查无此 slug~~ **撤回 —— 本条系审查方错误** | GPT-5.6 Sol/Terra/Luna 于 **2026-07-09** 发布 (openai.com/index/gpt-5-6/)；slug 存在于 codex 内置 `models.json`。`developers.openai.com/codex/models` 页面截至本次核验仍停在 gpt-5.5 —— **文档页滞后，不是 slug 不存在**。详见 §3.5 | 无需改。模型选型正确 |
| **P1-7′** | **(替代) sol/terra 在网关场景下会 400** —— codex 内置 `models.json` 对 `gpt-5.6-sol/terra/luna` 无条件硬编码 `use_responses_lite: true` / `multi_agent_version: "v2"` / `tool_mode: "code_mode_only"`，经 `include_str!` 编译进二进制，**无 provider 门控**；非 ChatGPT backend 不会远程刷新 model metadata → Azure 及任意自定义 `openai_base_url` 网关连吃两个 400 | [openai/codex#31882](https://github.com/openai/codex/issues/31882)，2026-07-09 提交、CLI 0.144.0、**当前 OPEN 无维护者回应**。报错 1: `X-OpenAI-Internal-Codex-Responses-Lite only supports function tools...`；强制 `use_responses_lite:false` 后报错 2: `Namespace 'collaboration' is reserved for encrypted tool use by this model` | RELEASE.md 明写"网关用户走 `openai_base_url`" → **该路径当前不可用**。在 platform-contracts.md 记为已知上游缺陷 + 给降级方案 (网关用户回退 gpt-5.5，或直连官方 endpoint)。与 P0-1 叠加: 网关路径双重损坏 |
| **P1-7″** | **`tool_mode: "code_mode_only"` 未评估** —— sol/terra 的模型级元数据强制 code-mode-only。工具调用形态改变会直接影响 CX hook matcher (`Bash` / `apply_patch`) 与 evidence-collector 的整条取证链 | 同 #31882 引用的 `models.json` 字段 | 列为 M3 dogfood **必测面**: 在 sol 下实测 `PreToolUse`/`PostToolUse` 是否仍按 `Bash`/`apply_patch` 派发 |
| **P1-7‴** | **`multi_agent_version` 模型级 vs 配置级优先级未知** —— `models.json` 对 sol/terra 硬编码 `"v2"`(luna 为 v1)，config.toml 又显式 `[features.multi_agent_v2] enabled = true`。两者精度关系无官方说明 | 同上 | 当前选型 (sol 主 + terra worker，均 v2) 自洽，不必改；记为 dogfood 观测项 |
| P1-8 | **evaluator VERDICT 决策表无优先级** —— "任一 P0 未修→FAIL"与"done_without_evidence ≥1→CONCERNS"可同时命中，表未声明 first-match / 取最严；"P0 已修"无对应行 | `agents/evaluator.md` 决策表 | 改为有序表 + 明写"自上而下首命中，多命中取最严"。delivery-gate 按 VERDICT 行解析 → 宽松行胜出即可 ship，这正是 sprint contract 想堵的"移动球门" |
| P1-9 | **npx 两条 allow 规则缺词边界** —— `Bash(npx playwright*)` / `Bash(npx ecc-agentshield*)` 无空格。官方: "`Bash(ls *)` matches `ls -la` but not `lsof`, while `Bash(ls*)` matches both" → 当前写法放行 `npx playwright-任意后缀`，npx 会从 registry 拉包并执行 | code.claude.com/docs/en/permissions | 改 `Bash(npx playwright *)` + `Bash(npx playwright)`，同理 ecc-agentshield |
| P1-10 | **`critic.md` off-by-one** —— 工作流第 5 步"综合评估 **6** 维度"，实际定义 7 个维度、输出表 7 行 | `agents/critic.md` | 改 7 |
| P1-11 | **RELEASE 关于 `permissionMode` 的断言有误** —— 写"官方 JSON schema 枚举…**无 `manual`**"。官方 settings 文档: "`default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`, **and `manual` as an alias for `default`** … requires v2.1.200 or later" | code.claude.com/docs/en/settings | 修措辞。结论 (维持 `default`) 不变，但依据是错的 —— 铁律[证据与出处]管的正是依据 |

---

## 3. P2

| # | 问题 | 修 |
|---|---|---|
| P2-12 | `iron-law-provenance.md` 只有 9 条，CX 宪法 10 条；CX 独有的 **铁律[Standards ≠ Codex .rules] 无溯源行**。两端文件字节完全相同 (2,795 B) = CC 版原样复制 | 拆成两份；补 CX 第 8 条出处 |
| P2-13 | **「维度」一词四义**: `三维度` (=3 个 agent) / `6 维度` (reviewer 检查项) / `7 维度` (critic) / `4 维` (evaluator 评分)。全在热路径 | 术语固化: agent 数用 **三件套**，检查清单用 **检查项**，评分用 **评分维度** |
| P2-14 | CC 端无 `CHANGELOG.md`，CX 有 37 KB | 补，或在 CC RELEASE 里指向 CX CHANGELOG |
| P2-15 | `settings.json` `enabledPlugins` 里 `feature-dev` 行缩进 4 空格 (兄弟行 2)。JSON 合法，但说明手改后没格式化 | 格式化 + validator 加 `json.dumps` round-trip 断言 |

---

## 3.5 撤回记录 · 本次审查自身踩的坑

P1-7 (「`gpt-5.6-sol/terra` 官方查无此 slug」) **是错的**。

事实: GPT-5.6 Sol / Terra / Luna 于 **2026-07-09** 正式发布 (openai.com/index/gpt-5-6/)。官方定位 —— Sol 旗舰、Terra 日常均衡、Luna 成本优先；OpenAI 明确"数字标识代际，Sol/Terra/Luna 是可独立演进的持久能力档"。slug 存在于 codex 内置 `models.json` 并被 issue #31882 逐字引用。

我错在: 把 `developers.openai.com/codex/models` 当成一手事实。该页截至本次核验 (2026-07-25) 仍只列到 `gpt-5.5` —— **发布后 16 天未更新**。

这条恰好是 9.9.6 自己在 `iron-law-provenance.md` 里列的待立候选第 4 条:

> **文档层不可作为一手事实** —— changelog / 文档页 / JSON schema 三者互相矛盾, 只有 schema 与源码 tag 能定音

本次审查给它添了一个新鲜、独立的事故样本 —— 而且是审查方自己踩的。**建议 9.9.7 把它从"待立候选"升为正式铁律**，判据补一条可执行的:

| 事实类别 | 一手源 (按优先级) |
|---|---|
| 模型 slug / 模型元数据 | 仓库内 `models.json` / `config.schema.json` → 厂商发布公告 → **最后**才是 docs 站点 |
| 配置键与枚举 | `config.schema.json` / 源码结构体 → docs |
| 事件 / 工具名 | 源码 dispatch 点 + 测试断言 → docs |
| 行为变更 | release tag / merged PR → changelog → docs |

推论: `platform-contracts.md` 现在只引 docs 站点 URL (CC 引 settings/model-config，CX 引 config-reference)。按上表应改为**双源**: docs URL + 对应 schema/源码路径与 tag。docs 滞后时后者定音。

---

## 4. 架构分析

### 4.1 分层是对的

```
宪法 (CLAUDE.md 21 行 / AGENTS.md 23 行)   ← 身份 + 铁律，不含操作
  ↓
skill 热路径 (SKILL.md, trigger-only description)
  ↓ 按需 Read
skill 冷路径 (references/*.md)
  ↓
agent frontmatter (角色 / 模型 / 权限 / 隔离)
  ↓
hook (机械门禁, fail-closed)
```

几个判断在业界上沿，明确记录为**不要动**:

| 决策 | 官方核验 |
|---|---|
| 不设 `CLAUDE_CODE_SUBAGENT_MODEL` | ✅ 官方: "overrides the per-invocation `model` parameter **and the subagent definition's `model` frontmatter**" —— 设了确实全矩阵静默失效 |
| agent frontmatter 用 `effort` 而非 `effortLevel` | ✅ 两个 key 都真实存在但在不同位置: frontmatter=`effort` (含 `max`)，settings.json=`effortLevel` (无 `max`)。写反即静默 no-op。这里写对了 |
| `worktree.baseRef = "head"` | ✅ 必需。默认 `fresh` 从 `origin/<default-branch>` 拉，红区 generator 看不到在途工作 |
| `tools` + `disallowedTools` 并存 | ✅ 非死配置。官方: "disallowedTools is applied first, then tools is resolved against the remaining pool" |
| CX 不注册 `Notification` / `PostToolUseFailure` | ✅ Codex 事件集确实无此二者 (完整集: PreToolUse / PermissionRequest / PostToolUse / PreCompact / PostCompact / UserPromptSubmit / SubagentStart / SubagentStop / Stop / SessionStart / SessionEnd) |
| CX matcher 去掉 `MultiEdit` | ✅ 正确。但 `Edit` / `Write` **要保留** —— 官方: "`apply_patch` … Match as `apply_patch`, `Edit`, or `Write`" |
| 铁律用 `铁律[名称]` 不用编号 | ✅ 这条是 CC 9 条 / CX 10 条编号错位下唯一有效的解耦手段 |
| 预算按**字节**截断而非字符 | ✅ 中文 1 字 3 字节，按字符算实际超 3 倍 |

### 4.2 熵在哪里

三个 P0、六个 P1，没有一个是"提示词写得不好"。全部是同一类:

> **相邻两层各自自洽，跨层契约无人验证。**

| 层间 | 当前保障 | 本次漏出的 bug |
|---|---|---|
| skill ↔ agent frontmatter | 人读 | P0-2 (`background:true` vs "收齐结果") |
| doc ↔ config | 人读 | P1-6 (hooks.md ↔ hooks.json 双向漂移) |
| config ↔ 平台真值 | 人读 | P0-1 (`base_url=""`)、P1-9 (词边界) |
| 结论 ↔ 依据 | 人读 | P1-11 (permissionMode 依据错但结论对) |
| skill 内部完整性 | 无 | P1-4 (孤立围栏) |
| 版本 N ↔ N-1 | **9.9.3 有，9.9.6 删了** | P1-5 (validator 自身回归) |

`validate-athena-9.9.6.py` 的断言形态基本是 `"字符串 X" in file_Y.read_text()`。76 PASS 证明的是**字符串在场**，不是**配置跑得起来**。`check_contracts` 全文读过 —— 最重的一条是"宪法实质行 ≤25"，其余是存在性。

这不是批评这一版。这是 9.9.3 → 9.9.6 之间**唯一一条被跨掉的护栏**: ratchet principle 被严格应用到了铁律 (`iron-law-provenance.md` 是个漂亮的机制)，却没有应用到 validator 自身。铁律只增不减，断言却掉了一半。

### 4.3 一句话结论

**9.9.6 有业界一流的静态门禁，和对自己为零的运行时门禁。**

RELEASE 已诚实标注"无 runtime 验证"。但把这句和上面的 finding 放一起看，结论更硬:

9.9.6 是对 9.9.3 的完整 fork = 按自家 PACE 属 **System 路径** → `plan → design → impl → runtime-verify → review → polish → ship`，`runtime-verify` **强制**、`delivery-gate` **fail-closed**。当前状态是跳过 runtime-verify 直接进 review。

P0-1 (装上就炸) 与 P0-2 (review 流程跑不通) 都是**一次真机 System 级 dogfood 的前 10 分钟**必然暴露的问题。这两条是 4.3 这句话的实证，不是推测。

---

## 5. 9.9.7 建议 (MUST / SHOULD / OUT)

### MUST

| # | 项 | 验收标准 (可机械判定) |
|---|---|---|
| M1 | 修 P0-1 / P0-2 / P0-3 | `openai_base_url` 键不存在于模板；`grep -c "background: true" agents/{reviewer,spec-compliance}.md` = 0；CX hooks.json 存在 `PreToolUse` matcher 含 `spawn_agent` 或 `Agent` |
| M2 | **validator 从存在性升级为契约断言** | 见下方 5 条子断言全部实现且各有 1 条失败样例 fixture |
| M2.1 | hooks 注册 ↔ 文档双向集合相等 | `set(hooks.json 中所有 command 的 basename) == set(hooks.md 表格引用的文件名)`，差集非空即 FAIL |
| M2.2 | agent frontmatter 键白名单 | 键 ∈ 官方 16 键 (`name/description/tools/disallowedTools/model/permissionMode/maxTurns/skills/mcpServers/hooks/memory/background/effort/isolation/color/initialPrompt`)；越界即 FAIL |
| M2.3 | config.toml 对官方 schema 校验 | 拉 `openai/codex/codex-rs/core/config.schema.json` 做 JSON Schema 校验；空串值单独断言 |
| M2.4 | 每个 SKILL.md: fence 数为偶 + frontmatter 可 `yaml.safe_load` | P1-4 直接被抓 |
| M2.5 | 回填 `check_package_parity` + `check_f_series_regressions` | 每个历史 P0 一条断言，**只增不删** —— ratchet 落到代码而非只落到铁律文档 |
| M3 | **一次真机 System 级 dogfood** | CC 2.1.219 + Codex 0.145.0 上完整跑一遍 `plan→design→impl→runtime-verify→review→polish→ship`，产出 `runtime-verify.md`。**必测面**: (a) sol 的 `code_mode_only` 下 CX hook matcher 是否仍按 `Bash`/`apply_patch` 派发 (P1-7″)；(b) `approval_policy=never` + `danger-full-access` 组合；(c) 后台 worktree 自动 PR 是否被 push 门禁拦住 |
| M4 | 修 P1-4~P1-11 | 逐条 |

### SHOULD

| 项 | 理由 |
|---|---|
| **待立候选「文档层不可作为一手事实」升为正式铁律** | 本次审查自身踩中 (§3.5)。补可执行的**源优先级表**: 模型元数据 → `models.json`；配置枚举 → `config.schema.json`；事件/工具名 → 源码 dispatch + 测试；行为变更 → release tag/PR。docs 站点排最后 |
| `platform-contracts.md` 改双源引用 | 现只引 docs URL；应加对应 schema/源码路径 + tag，docs 滞后时后者定音 |
| iron-law-provenance 双端拆分 + 补 CX 第 8 条 | ratchet 对该条当前失效 |
| evaluator VERDICT 表改有序 + "首命中，多命中取最严" | delivery-gate 按此行解析，歧义 = 可 ship 的漏洞 |
| 术语表 (三件套 / 检查项 / 评分维度) | 热路径四义 |
| 网关路径降级方案写进 platform-contracts | #31882 未修前，`openai_base_url` + sol/terra = 400 |
| CC 补 CHANGELOG | 双端不对称 |

### OUT OF SCOPE (本版明确不做)

| 项 | 理由 |
|---|---|
| 新增 skill / 新 stage | 无 dogfood 数据 —— 铁律[反过度工程]；v9.7 的 24 文件先例 |
| 26 个 skill 合并/删减 | 同上。9.9.6 "一个未删未并"是对的，等 M3 的路径使用数据 |
| 改模型选型 | sol/terra 选型正确 (2026-07-09 发布)。#31882 是上游缺陷，不是选型错误 —— 记录 + 降级，不换模型 |
| CX 补 `Notification` 等价物 | 官方无此事件 —— 铁律[四原语]「不伪造对称工具」 |

---

## 6. 反驳痕迹 (供未来审计)

| 我一度想提的 | 反驳 | 结论 |
|---|---|---|
| `tools` + `disallowedTools` 冗余，删 `disallowedTools` | 官方明确两者都生效 (disallowed 先应用)；且属防御纵深，铁律[反过度工程]自带豁免 | **砍** |
| `Bash(ls *)` 等 allow 规则可被 `&&` 绕过 | 官方: "Claude Code is aware of shell operators … `Bash(safe-cmd *)` won't give permission to run `safe-cmd && other-cmd`"，识别 7 种分隔符 | **砍**。只留 npx 词边界一条 (P1-9) |
| CC/CX 宪法条数不一致 (9 vs 10) 是 parity 缺陷 | "引用铁律用名称不用编号"已解耦；条数差异源于 CX 平台特异性，强行对齐反而是伪对称 | **降级为 P2** (只补溯源行) |
| 26 个 skill 太多，该合并 | 无痛点数据。9.9.6 已把热路径压到 26.7 KB，成本问题已解 | **砍** |
| CX `approval_policy=never` + `danger-full-access` 太激进 | 官方无针对此组合的警告；且 pre-bash-guard 已按 CC 覆盖面对齐加固 | **砍**，但列为 M3 dogfood 必测面 |

---

## 7. 一句话

**先修 3 个 P0，再把 validator 从"字符串在场"改成"契约成立"，然后跑一次真机 System dogfood —— 这三步之外的任何新功能，在 9.9.7 都是过度工程。**

---

## 参考

- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/permissions
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/worktrees
- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://raw.githubusercontent.com/openai/codex/main/codex-rs/core/config.schema.json
- https://raw.githubusercontent.com/openai/codex/main/codex-rs/model-provider-info/src/lib.rs
- https://github.com/openai/codex/pull/23757
- https://github.com/openai/codex/releases/tag/rust-v0.133.0
- https://developers.openai.com/codex/models  ⚠️ 截至 2026-07-25 仍停在 gpt-5.5，晚于发布 16 天 —— 见 §3.5
- https://openai.com/index/gpt-5-6/  (GPT-5.6 Sol/Terra/Luna, 2026-07-09)
- https://github.com/openai/codex/issues/31882  (sol/terra/luna 硬编码 responses-lite，网关 400，OPEN)
