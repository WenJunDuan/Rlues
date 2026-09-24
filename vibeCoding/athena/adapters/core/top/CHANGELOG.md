# Athena CHANGELOG

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
- 项目 `.ai_state` 需迁移：`athena migrate --to 10.1`（见 AI-MIGRATION-GUIDE.md）。
- CX 规范目录仍为 `~/.codex/standards/`，文件名改为 coding / security / ui / docs / git / shell。
- 证据只认 `athena run` 的记录；手写证据文件不再被读取。

### 已知取舍与未做
- S7（Pi 0.87 Stop 硬停）、S8（模型实测评测）取消：Pi 仍以 followUp 提示代替硬停。
- test_build 对 prompts 层整体声明 delta，逐文件约束由 test_prompts 承担。
- 真实安装（`~/.claude`、`~/.codex`）需用户执行 `athena install`。

### 验证
- `vibeCoding/athena/evals/fixtures`：154 个测试通过；9.9.9 回归（athena999）231 通过。
- 每片独立 review 2–5 轮，结论与处置见各 sprint 的 reviews/。
