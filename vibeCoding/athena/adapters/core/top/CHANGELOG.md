# Athena CHANGELOG

## 10.5.0 — 插件就绪（候选，2026-10-04）

基线 10.1.0（含其后 main 上的未发布项）。一句话：CC / Codex 各出一个自带门禁核的插件壳，Pi 拿到硬 Stop，门禁报错自带修法，提示词 v3。**候选**：无 tag、未装机；发布门见 RELEASE.md。

### 新增
| 项 | 说明 |
|---|---|
| CC 插件壳 | `dist/claude-plugin/<ver>/`：`.claude-plugin/plugin.json`、`hooks/hooks.json`（9 事件 → `${CLAUDE_PLUGIN_ROOT}/gate/hook.cjs --platform cc`）、vendored `gate/`（与 `dist/athena` 同字节）、`bin/athena`、skills + agents；宪法经 SessionStart 注入（`ATHENA_CONSTITUTION`） |
| Codex 插件壳 | `dist/codex-plugin/<ver>/`：`plugin.json`（`extensions["com.openai"].hooks`）、`hooks/hooks.json` → `${PLUGIN_ROOT}/gate/hook.cjs --platform cx`、vendored `gate/`、skills；hooks 须在 `/hooks` 受信 |
| Pi 硬 Stop | `agent_before_settle` → `{entries, continue: true}`；同因熔断上限；Pi < 0.87 回退 followUp。codemode 外层放行、脚本内工具照常过门；peer `*` |
| `athena run --rebind` | 当前树重跑最后一条 test/typecheck 证据，记新 tree_sha；失败不记 PASS |
| `athena writer dispatch/collect` | worktree + `external-writer.json` + `parallel_writers`；merge-tree 探冲突、`--ff-only`、还原 |
| `athena status` | AC 覆盖矩阵 + ship 预检 |
| `athena issue --type gate` | 追加到上游 FEEDBACK（`ATHENA_FEEDBACK` / `~/.athena/config.json`），缺配置不失败 |
| `athena doctor` | 插件形态报告；同端双装 WARN；只有插件形态 → WARN `plugin form only` + 安装器才带的部分（CC：rules、CLAUDE.md；CX：config.toml、AGENTS.md、`/hooks` 受信），不算 FAIL；两种形态都没有仍 FAIL `not installed` |

### 修复
- G-018：嵌套 worktree 的 `<wt>/.ai_state/…` 被算实现写入 → 按任一已登记 worktree 根的 `.ai_state` 排除；worktree 内源码无 AC 仍拦。
- 报错带修法：`run` 不可证明、`review accept` 拒收、covers 格式错时 stderr 给修正样例与下一步命令。

### 提示词 v3
- 宪法：「完成」改点名早停形态 + 末段自检；范围即交付物；例行 athena 命令预授权；进度更新一句。
- rules：删除优于兼容；新增依赖先查已有；测试跟 AC / 按路径；临时方案写移除条件；P0 行数/常量条降 P1。
- PACE：黄区默认主 agent 直做，子 agent 只为隔离或并行；platform.md 补 Pi 硬停、插件形态、code mode、待验证项。
- 包内去模型钉版与 effort：CC `effortLevel`；Codex `model` / `model_reasoning_effort` / `plan_mode_reasoning_effort`。

### 并入（10.1.0 之后 main 上的未发布项）
- CC / CX 包配置对齐官方文档：官方插件市场名、密钥 deny、危险操作 ask、去掉模型钉版；Codex 首装改官方默认 `on-request` + `workspace-write`。
- 安装器：包 `env` 此前被整体丢弃，改为补缺、用户优先；`permissions.ask` 与 `deny` 同为并集。
- 仓库整理：9.9.x 及更早版本归档到 `vibeCoding/old/`；安装、迁移、发布三份文档移到 `vibeCoding/athena/` 顶层。

### 破坏性变更
- `.ai_state`：无。schema v2 不变，`_index.md` `version: "10.1"` 是状态代际，`athena init` / `migrate` 继续写 `"10.1"`；`athena migrate --to 10.1` 不变。
- 黄区默认改为主 agent 直做；新装不再带包内模型 / effort 默认（已装用户配置不变）。

### 已知取舍与未做
- 行为评测（D-014）、探针 P1–P8 未跑，待本机；插件清单未经 `claude plugin validate` / Codex 实装；Pi 扩展只做了类型检查。
- 插件形态未自足：skills / agents 正文仍写安装器路径；同端不可双装。
- Stop 三连拦熔断保留。

### 回滚
| 要回滚什么 | 怎么做 |
|---|---|
| 本机安装 | `athena rollback` |
| 插件形态 | 停用 / 卸载插件 |
| 项目 `.ai_state` | 不需要（未改） |
| 源码 | 10.1.0 `f4af800`；10.5 基线 `1c1cd73` |

## 10.1 — 单一门禁核 + 状态 v2 + 提示词 v2（2026-09-24）

基线 9.9.9。一句话：9.9.x 靠「三端各一套 hook + 长宪法劝导」，10.1 改为「一个 JS 门禁核机械强制 + 一个 CLI 记账 + 一份短宪法」。

### 新增
| 项 | 说明 |
|---|---|
| 单源构建 | `vibeCoding/athena/build.mjs`：core + adapters → claude / codex / pi / athena 四个 dist；`rename` / `core_map` / `{{athena:!VAR}}` 模板；stages.md 与 contracts.json 由 `core/pace/stages.yaml` 生成 |
| 门禁核 | `~/.athena/current/hook.cjs`，三端同一套规则：硬门 H1 design-first、H2 证据、H3 review、H4 红区隔离、H5 shell；提示项 A1–A10；豁免 ≤14 天（H2/H3 无豁免）；Stop 三连拦熔断 |
| 证据 | `athena run [--covers ACn] -- <cmd>`：记录 exit + 源码树 sha，判定可证明性（后台、`||`、遮蔽、无 pipefail 等为 unprovable） |
| review 两步 | `athena review prepare` → 独立 reviewer → `athena review accept`；绑定源码树与 AC 摘要；三端同一 reviewer 合同；CC 可选 workflow |
| 状态 v2 | `_index.md` 路由器（≤3 KB）、sprint = design + log (+ review.json)、`issues.md` 单一问题账、`queue.md`、按月归档；CLI：`init` `status` `sprint` `ship` `issue` `tidy` `migrate` |
| 安装器 | `athena install / rollback / doctor`：`~/.athena/<ver>` + `current` 链接；合并而非覆盖用户 settings/hooks/config；事务式备份；9.9.9 残留移入备份 |
| 提示词 v2 | 宪法三端同源 1.6 KB（原 4 KB+）；rules 637 → ~140 行并带 CC 路径作用域，`core/rules.md` 逐条溯源；skills 单源、每个 ≤60 行；agents 4 个（architect / generator / polish-worker / reviewer），CC `omitClaudeMd` |

### 删除 / 合并
- 9.9.x 全部 CC/CX hook、Pi cc-core、review-binding、REVIEW.md、setup-athena.py、athena-migrate。
- skills：antigravity 删；athena-preferences → athena-init；athena-checkpoint、athena-issue → athena-status；compound → pace/references/decisions.md。
- agents：critic、evaluator、spec-compliance、docs_researcher、pr_explorer。
- 产物：tdd-evidence.yaml、evidence.yaml、checklist.yaml、review-packet.md、cleanup-pass.md、route-note.md、implementation-review.md、session-log.md（由 `athena run` 证据、review.json、log.md 取代）。
- 9 条编号铁律（改由门禁机械强制）、「INTJ 风格」、「CC 无原生 /goal」。

### 破坏性变更
- 项目 `.ai_state` 需迁移：`athena migrate --to 10.1`（见 MIGRATION.md；安装见 INSTALL.md，发布声明见 RELEASE.md）。
- CX 规范目录仍为 `~/.codex/standards/`，文件名改为 coding / security / ui / docs / git / shell。
- 证据只认 `athena run` 的记录；手写证据文件不再被读取。

### 已知取舍与未做
- S7（Pi 0.87 Stop 硬停）、S8（模型实测评测）取消：Pi 仍以 followUp 提示代替硬停。
- test_build 对 prompts 层整体声明 delta，逐文件约束由 test_prompts 承担。
- 行为评测门豁免（`.ai_state/decisions/2026-09-24-decision-athena-10-1-release-gate.md`，债务 D-014，10.2 恢复）。
- 部署范围 CC + CX；Pi 不部署（同上 decision）。

### 回滚
| 要回滚什么 | 怎么做 |
|---|---|
| 本机安装（`~/.claude` `~/.codex` `~/.athena`） | `athena rollback`：事务式，按 install 时备份逐字节恢复到 9.9.9；`athena doctor` 应报 `not installed` |
| 项目 `.ai_state`（v2 → v1） | 回到 tag `pre-athena-10.1-state`（`athena migrate` 实迁前自动打）。**只覆盖 `.ai_state` 迁移**：该 tag 在 10.1 代码合入之后，不能用来回滚代码 |
| 源码（查看或回退到 10.1 之前） | `d42979a`（S0 热修后、`athena-10.1` 合入前的最后一个 main 提交）；10.1 代码合入点为 `cfc76aa` |

### 验证
- `vibeCoding/athena/evals/fixtures`：156 个测试通过；9.9.9 回归（athena999）231 通过。
- 发布前：真机 `athena install --dry-run`、quantum-agent `athena migrate --dry-run`（Blockers 0）；安装后 `athena doctor` no drift。
- 每片独立 review 2–5 轮，结论与处置见各 sprint 的 reviews/。
