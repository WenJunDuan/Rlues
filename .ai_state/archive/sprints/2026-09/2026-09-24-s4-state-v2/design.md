---
sprint_slug: "2026-09-24-s4-state-v2"
path: "System"
created: "2026-09-24"
roadmap: "athena-10-1"
item: "s4-state-v2"
branch: "athena-10.1"
base_commit: "c2d4587"
---

# Design — S4 · 状态 v2（schema + CLI + 自动归档 + 迁移）

> 设计真相：`roadmap/athena-10-1/design.md` §7、§11.3；`refs/ai-state-v2.md`。本片只写增量与偏差。

## 方案

- 模板 `gate/templates/`（随核心安装到 `~/.athena/<ver>/templates`）：_index.md、design.md、bugfix-design.md、requirement.md、roadmap.md、items.yaml、issues.md、decision.md、log.md、queue.md。
- CLI（`gate/cli/*.cjs` + `gate/cli/lib/*.cjs`）：status、sprint start/stage/pause/resume/drop、ship、issue add/close/list、tidy、migrate。
- 写 `_index` / `items.yaml` 一律**键级原地改写**：保留注释与未知键；v1 拼写（current_sprint_slug / current_roadmap_slug / route_history / sprint_slug）与 v2 拼写（sprint / roadmap / route / sprint）按文件现有键选择 —— 构建期 Rlues（v1）与 v2 项目同一套代码。
- ship：H2/H3 严格重跑（未知状态直接拒绝）→ 归档前运行时读取检查（`git grep` 仓库内对该 sprint 路径的引用，排除 .ai_state）→ 写 evidence.yaml 汇总（每条 AC → 覆盖记录 + 最终 PASS 记录）→ sprint 目录整体移到 `archive/sprints/YYYY-MM/<slug>/`（gitignored 文件随目录走）→ 原始证据 jsonl 移到 `.runtime/archive/evidence/` → items done{commit,review} → queue.md 删行 → `_index` 回 idle + route 行 → `git add` 状态路径（不提交）。
- 月度打包（保留窗 = 当月 + 上月不打包）：`archive/sprints/YYYY-MM/` → `archive/YYYY-MM.tar.zst`（无 zstd 时 `.tar.gz`），展开目录 `git rm`；`archive/README.md` 重定向表追加。
- session-start 注入（AC5）：路由摘要、生效豁免、待裁定置顶、`resume_when: "after <item>"` 已满足的 deferred/paused 项、梳理阈值（A7）。
- migrate --to 10.1：dry-run 只出报告；实迁要求工作树干净并打 tag `pre-athena-10.1-state`；历史档正文不改（NV-D10）。

### 与 10.1 设计的偏差（已裁量）

| 设计原文 | S4 做法 | 理由 |
|---|---|---|
| 模板在 `core/templates` | `gate/templates` | CLI 运行时要读模板，随核心安装；core/package 只装进各平台 skills |
| AC8「门禁代码 ≤3,000 行」 | 钩子路径（hook/core/lib/rules/platform）≤3,000；CLI（cli/**）单文件 ≤300、不计入合计 | CLI 不在每次工具调用的热路径上 |
| `archive/YYYY-MM.tar.zst` | 有 `zstd` 用 .tar.zst，否则 .tar.gz | macOS 默认无 zstd |
| AC4 两仓 dry-run | 只跑 Rlues；quantum-agent 由用户自行迁移（2026-09-24 用户指示） | 用户裁定 |
| 迁移/归档安全 | 只暂存 CLI 自己移动或写入、且原本已跟踪的文件；未跟踪/忽略文件随目录移动但不入库，含此类文件的月份不打包；ship/drop/migrate 先做全部可失败检查再写；migrate 撞名、运行时读取即拒绝 | review r1 P0/P1 |
| items `done{commit,review}` | `done{after,review}`：after = ship 所落在的 HEAD | ship 只暂存不提交，拿不到 ship 提交自身的 sha |
| migrate 运行时读取检查 | 命中即拒绝；`--allow-reads "<理由>"` 可豁免并写进报告 | Rlues 冻结的旧版 harness 源码注释里大量字面提及 `.ai_state/...`，不应为迁移改历史源 |
| 路径型 ignore 规则 | 归档后仍须忽略的文件写入 `.ai_state/archive/.gitignore` 精确条目 | 防止迁移后秘密文件被下一次 `git add -A` 提交 |
| resume_when 自动判定 | 仅 `after <roadmap>/<item>` 或 `after <item>` 形式可机判（该 item done）；其余原样列出 | 自由文本无法机判 |
| sprint 目录名 | 默认 `YYYY-MM-DD-<item>`，`--slug` 可覆盖 | 与 S0–S2 现有命名一致 |

## 验收标准 (Done Contract)

- AC1: v2 模板齐全；`athena sprint start` 生成的 `_index` ≤3 KB、design 带 req/roadmap/item/path/base_commit 与 `- AC1:` 占位示例（非有效 AC，H1 仍拦）；v1 与 v2 `_index` 都能被 CLI 原地改写且保留注释。
- AC2: status / sprint start·stage·pause·resume·drop / ship / issue add·close·list(--export) / tidy 全部可用，错误用法非零退出并给出合法形态。
- AC3: ship 通过时一次完成归档 + items done + queue 删行 + `_index` idle + evidence.yaml 汇总；H2/H3 不过即拒绝且不动任何文件；仓库内代码读取该 sprint 路径时拒绝归档并列出命中；gitignored 文件随目录归档；上上月及更早目录打包。
- AC4: `athena migrate --to 10.1 --dry-run` 在 Rlues 跑通并出报告到 `docs/reports/`（dry-run 不改任何文件）；实迁在临时仓 fixture 上往返（tag 回滚）。
- AC5: session-start 注入含路由摘要、生效豁免、待裁定、resume 就绪项、梳理提示。
- AC6: v2 模板与 CLI 不写 counts / fingerprint / platform 探测字段；探测类字段迁到 `.runtime/probe.json`；`.snapshots/` 由迁移移入 `.runtime/`；dist 无 index-updater（S2 已删，fixture 守住）。

## 允许写集

`vibeCoding/athena/gate/{cli,templates}/**`、`gate/core.cjs`（注入）、`gate/lib/*`（只读辅助）、`vibeCoding/athena/evals/fixtures/test_state_*.py`、`evals/fixtures/test_gate_contracts.py`（预算口径）、本 sprint 文书、`_index.md`、`items.yaml`、`docs/reports/`（迁移报告）。

## 不做

Rlues 实迁（S9）；review CLI（S3）；宪法/skills 文案（S5）。
