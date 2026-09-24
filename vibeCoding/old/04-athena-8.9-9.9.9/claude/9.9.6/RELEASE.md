# Athena Claude Code 9.9.6 — DRAFT

Status: reviewable draft; **not released**. 修复后本地 validator **63 PASS / 0 FAIL / 0 SKIP**；完整 runtime-verify 尚未执行。

Baseline: 不可变的 `vibeCoding/{claude,codex}/9.9.3`。9.9.6 是完整 fork。

## 平台合同

- 目标 Claude Code 2.1.219+ / Opus 5 与 Codex CLI 0.145.0+ / GPT-5.6。
- **不设全局 subagent model override**。`CLAUDE_CODE_SUBAGENT_MODEL` 官方定义即"overrides the subagent definition's `model` frontmatter"，设了它整个角色矩阵静默失效，因此发行模板不写。
- 删除 dated Opus/Sonnet pin 与旧 Sonnet 全局 subagent override；保留 root `effortLevel=xhigh`、Fable 5 pin、privacy/attribution/installation-check，并把 API timeout 更新为 600 秒。Tool Search 默认已开，不重复配置。
- `settings.proxy.json` 提供 `127.0.0.1:6152/6153` 本地代理 overlay，默认不加载；用 `claude --settings ~/.claude/settings.proxy.json` 显式启用。
- 保留 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` 作为隐私保守默认；迁移保留用户现值。
- `permissions.defaultMode` 维持规范值 `default`；Claude Code 2.1.200+ 也接受 `manual` 作为 `default` alias，迁移须保留用户现值。
- Codex 用内置 `model_provider = "openai"`(保留 ID，不得自定义)，网关用户走 `openai_base_url`；保留 1M context、900K compact、Memories、warning、WSL acknowledgement、`[desktop]` 与 plugins；只删空 provider、stable default-on feature 重复开关和冗余 skill 注册。
- 保留 `[features.multi_agent_v2] enabled=true`(0.145.0 stable 但仍 opt-in) 与 `hide_spawn_agent_metadata=false` —— 后者缺失会让 Sol 下 `spawn_agent` 丢掉 model/reasoning_effort (openai/codex#31814)。

## 角色矩阵

| 端 | 高价值 | 实现/审查 |
|---|---|---|
| CC | `architect`/`critic`=`fable`，`evaluator`=`opus` | `generator`/`reviewer`/`spec-compliance`/`polish-worker`=`opus` |
| CX | `architect`/`critic`/`evaluator`=`gpt-5.6-sol` | 其余 6 个=`gpt-5.6-terra` |

root effort=`xhigh`，各 agent frontmatter 保留 3×xhigh + 4×high 的角色覆盖。

## 常驻预算(实测字节，非估算)

| 指标 | 9.9.3 | 9.9.6 | 门 |
|---|---:|---:|---:|
| CC SessionStart | 7,801 | **2,316** | ≤2,500 |
| CX SessionStart | 7,631 | **2,241** | ≤2,500 |
| CC breadcrumb | 797 | **291** | ≤400 |
| CX breadcrumb | 1,008 | **295** | ≤400 |
| CC skill catalog | 8,621 | **3,149** | ≤4,000 |
| CX skill catalog | 8,834 | **3,744** | ≤4,000 |
| SKILL.md 热路径合计 | 93,327 | **~26,700** | 单文件 ≤4,096 |

做法：SessionStart 改字段白名单注入(不再整段注入 `_index` frontmatter)；摘要截断改**按字节**(中文 1 字 3 字节，按字符算实际超预算约 3 倍)；breadcrumb 按行裁剪；26 条 description 改 trigger-only；10 个超标 skill 正文下沉 `references/playbook.md`(原文未改，可逆)。

## 安全与并发

- **`_index.md` 并发写竞态**(9.9.3 起存在)：同事件多个 hook 并发做 read-modify-write，后写覆盖先写，丢的是 `design_changed_after_impl` 这类门禁标记且不报错。新增 `_index-io.cjs` / `_index_io.py`：O_EXCL 锁(含 stale 打破) + tmp/rename 原子替换，双端 3 个写者全部接入。
- **Codex `pre-bash-guard` 加固**：9.9.3 是平坦正则，覆盖面约为 CC 的 1/4，而 Codex 跑在 `approval_policy=never` + `danger-full-access` 下。实测可绕过并已修复：`rm -rf /*`、`rm -rf //`、`rm -rf /.`、`rm -rf $HOME/`。本版对齐 CC 的 shell 分析器(递归命令替换、路径归一化、env 前缀剥离、`bash -c`/`eval`/`xargs` 内层重分析、`git -C` 选项定位、管道 `curl|wget→shell`、深度上限、解析失败 fail-closed)。**已知共有限制**：`` rm -rf `echo /` `` 双端都拦不住 —— 替换结果需执行才可知。
- **副作用 skill 锁隐式调用**：`athena-setup/migrate/init/preferences` —— CC 用 `disable-model-invocation: true`(官方："Only you can invoke"，且描述不进 context)，CX 用 `<skill>/agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`。

## PACE / Skills / Hooks

- **sprint contract(新)**：`checklist.yaml` 顶部落 `done_contract`，把验收标准写成可机械判定的条件。generator 与 evaluator 判**同一份契约**；evaluator 不得另造判据，generator 不得自行放宽；要改回 design 改。
- **`/goal` 双端对齐**：Codex goals 自 rust-v0.133.0 起 default-on 且不再 experimental，CX 不再自造 runtime-verify 循环(铁律[不抱金饭碗讨饭])。
- **CX 补齐可观察 hook**：`design-change-detector.py`、`pace-continuator.py`，并用 Codex 0.145 function-tool PreToolUse 的 `spawn_agent|Agent` matcher 做红区 worktree 前置阻断；SubagentStart audit 作为纵深证据。
- **铁律溯源表(新)**：`rules/iron-law-provenance.md` / `standards/iron-law-provenance.md`，冷路径不注入，把 9 条铁律逐条挂到 `compound/` 的具体事故，并列出 5 条 9.9.6 待立候选。
- PACE 4 核心 + 5 条件 stage、红黄绿区、2+1 review、fail-closed gates 语义**不变**。26 个 skill 一个未删未并。

## Opus 5 行为迁移

删除跨模型遗留的自我验证劝导：宪法第 6 行"自跑命令/测试并读取输出证明完成"、铁律5"报'完成'附可复核命令输出/diff"。完整分类见 sprint 的 `verification-inventory.md`。TDD、真实测试、交付证据合同**未删** —— 它们由 gate 机械核验，不是 prompt 劝导。

## 已知未验证 (交付给 review 的显式风险面)

1. **无完整 runtime-verify。** 已完成临时 HOME 双端 fresh setup 与 exact Codex 0.145.0 `config.load`；尚未在 exact CC 2.1.219/Codex 上跑完整 PACE 流程。
2. **CX worktree 门禁仍需 exact-host dogfood。** `spawn_agent|Agent` 已接入 PreToolUse 真阻断，SubagentStart 事后审计记录由 delivery-gate 消费；仍须在 exact 0.145.0 Sol `code_mode_only` 路径实测 matcher 与 exit-2 阻断 wire。
3. **GPT-5.6 gateway 上游风险。** openai/codex#31882 在 Codex 0.144.0 + Azure OpenAI 复现 Responses-Lite/collaboration 400；这不证明所有自定义 base URL 必现。release 前必须对实际 gateway dogfood，未通过时使用该 endpoint 已验证支持的 provider/model 组合。
4. `gpt-5.6-terra` 与 `fable` alias 在本账号下的可用性未实跑(fable 需 org 权限，ZDR 下不可用)。
5. 无 A/B eval，无 migration/rollback fixture，无 N≥3 统计。
