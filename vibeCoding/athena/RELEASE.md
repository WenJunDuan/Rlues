# Athena 10.1.0 发布声明

| 项 | 值 |
|---|---|
| 版本 | 10.1.0（minor，基线 9.9.9） |
| 日期 | 2026-09-24 |
| Tag | `v10.1.0` → `f4af800` |
| 部署范围 | Claude Code + Codex；Pi 构建与测试覆盖，默认不部署 |
| 安装 | 见 `INSTALL.md` |
| 项目状态迁移 | 见 `MIGRATION.md` |
| 完整变更 | `CHANGELOG.md` |

## 一句话

9.9.x 是「三端各一套 hook + 长宪法劝导」，10.1 改成「一个 JS 门禁核机械强制 + 一个 `athena` CLI 记账 + 一份短宪法」。

## 主要变化

| 项 | 内容 |
|---|---|
| 单源构建 | `vibeCoding/athena/` → `dist/{claude,codex,pi,athena}`；版本号只来自 `VERSION` |
| 门禁核 | `~/.athena/current/hook.cjs`，三端同一套规则：H1 design-first、H2 证据、H3 review、H4 红区隔离、H5 shell；提示项 A1–A10 |
| 证据 | `athena run [--covers ACn] -- <cmd>`，绑定源码树 sha；手写证据不再被读取 |
| review | `athena review prepare` → 独立 reviewer → `athena review accept` |
| 状态 v2 | `_index.md` 路由器 ≤3 KB；sprint = design + log (+ review.json)；`issues.md` 单一问题账；按月归档 |
| 安装器 | `athena install / doctor / rollback`，事务式、合并不覆盖 |
| 提示词 v2 | 宪法三端同源 1.6 KB；rules ~140 行；skills 单源 |

## 破坏性变更

- 项目 `.ai_state` 需迁移（`athena migrate --to 10.1`）。
- 9.9.x 的 hook、`setup-athena.py`、`athena-migrate`、critic / evaluator / spec-compliance 等全部退役。
- 证据只认 `athena run`。

## 发布门

| 门项 | 结果 |
|---|---|
| fixture 三端全绿 | 通过（发布时 156/156） |
| 行为评测对 9.9.9 不退化 | **豁免**：`.ai_state/decisions/2026-09-24-decision-athena-10-1-release-gate.md`；债务 D-014，10.2 恢复 |
| Rlues + quantum-agent 迁移 | dry-run 通过（Blockers 0），两仓均已实迁 |
| 安装 / 回滚演练 | fixture 逐字节回滚验证；真机 dry-run → install → `doctor: no drift` |
| quantum 真实 Feature sprint | major 条件，10.1 不适用；发布后验证 |

## 已知限制

- 无「质量不退化」的量化证据（见上）。
- Pi 仍以 followUp 提示代替 Stop 硬停（S7 未做）。
- Stop 连续三次拦截后熔断放行，并写入 `issues.md`。
- 用户 `~/.claude/settings.json` 里旧版遗留的无效插件键不会被安装器清理。

## 回滚

| 回滚什么 | 怎么做 |
|---|---|
| 本机安装 | `athena rollback` |
| 项目 `.ai_state` | tag `pre-athena-10.1-state`（仅状态迁移，见 `MIGRATION.md` §5） |
| 10.1 之前的源码 | `d42979a`（10.1 合入点 `cfc76aa`） |

## 未发布（main 上，10.1.0 之后）

- CC / CX 包配置对齐官方文档：官方插件市场名、密钥 deny、危险操作 ask、去掉模型钉版；Codex 首装改官方默认 `on-request` + `workspace-write`。
- 安装器：包 `env` 此前被整体丢弃，改为补缺、用户优先；`permissions.ask` 与 `deny` 同为并集。
- 仓库整理：9.9.x 及更早版本归档到 `vibeCoding/old/`；安装、迁移、发布三份文档移到 `vibeCoding/athena/` 顶层。
