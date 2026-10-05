# Athena 10.1.5 发布声明（候选）

> **候选，未发布**：Mac 发布门已通过，待用户裁定合入 main 与本地 tag。2026-10-05 范围收窄（方案 A）：本版只承诺**安装器形态**；CC / Codex 插件壳随包构建、标 experimental。真机安装与 P8 演练后已回滚到 10.1.0，尚未正式部署 10.1.5。

| 项 | 值 |
|---|---|
| 版本 | 10.1.5（基线 10.1.0；版本编号经用户纠正） |
| 日期 | 2026-10-05（Mac 发布门验证） |
| Tag | 无（候选） |
| 分支 | `athena-10.1.5` |
| 部署范围 | Claude Code + Codex 安装器形态；CC / Codex 插件壳 experimental（只验到构建与组件发现，不作发布承诺）；Pi 构建与测试覆盖，默认不部署 |
| 安装 | 见 `INSTALL.md`；构建产物在 `dist/<platform>/10.1/` |
| 项目状态迁移 | 无：`.ai_state` schema 仍是 v2（`_index.md` `version: "10.1"`），10.1 项目直接可用 |
| 完整变更 | `CHANGELOG.md` |

## 一句话

安装器形态收尾：门禁报错自带修法，rebind / writer / status 三个 CLI，Pi 拿到硬 Stop，提示词 v3；CC / Codex 插件壳随包提供，experimental。

## 主要变化

| 项 | 内容 |
|---|---|
| CC 插件壳（experimental） | `dist/claude-plugin/10.1/`：hooks → `${CLAUDE_PLUGIN_ROOT}/gate/hook.cjs`、`bin/athena`、skills + agents；宪法由 SessionStart 经 `ATHENA_CONSTITUTION` 注入。带不走：path-scoped rules、`settings.json` permissions/env、review workflow → 仍需安装器 |
| Codex 插件壳（experimental） | `dist/codex-plugin/10.1/`：默认发现 `hooks/hooks.json` → `${PLUGIN_ROOT}/gate/hook.cjs`、skills；根清单不带 `$schema`（见已知限制 U-001）。带不走：`config.toml`、`AGENTS.md`、`standards/`、agents、`bin/`；hooks 装后须在 `/hooks` 受信 |
| Pi 硬 Stop | `agent_before_settle` 返回 `{entries, continue: true}`，ship 缺证据/审查时续跑；Pi < 0.87 回退 followUp 软纠偏。codemode：外层调用放行，脚本内 `write`/`edit`/`bash` 照常走 H1/H5。peer 放宽为 `*` |
| G-018 修复 | `.ai_state` 排除按任一已登记 worktree 根判；嵌套 worktree 内写 sprint design 不再被 H1 拦，worktree 内源码无 AC 仍拦 |
| 报错带修法 | `athena run` 不可证明、`review accept` 拒收、covers 格式错：stderr 给可复制的修正样例与下一步命令 |
| `run --rebind` | 在当前树重跑最后一条 test/typecheck 证据并记新 tree_sha；重跑失败不记 PASS |
| `writer dispatch/collect` | dispatch 建 worktree + `external-writer.json` + `parallel_writers≥2`；collect 用 merge-tree 探冲突、`--ff-only`、还原 |
| `status` | AC 覆盖矩阵 + ship 预检（缺哪条证据、H2/H3 现在会拦什么；10.1 代码里没有轻门禁，故不报） |
| `issue --type gate` | 追加一行到上游反馈账（`ATHENA_FEEDBACK` 或 `~/.athena/config.json` 的 `feedback`；Rlues 内为 `.ai_state/docs/research/athena-downstream-feedback.md`）；缺配置不失败 |
| `doctor` | 分别报告安装器形态 / 插件形态；同端双装 WARN；只有插件形态时 WARN「plugin form only」并列出安装器才带的部分，不算 FAIL |
| 提示词 v3 | 点名早停形态 + 末段自检；范围即交付物；例行 athena 命令预授权；黄区默认主 agent 直做；删除优于兼容；新增依赖先查已有；测试跟 AC；包内去掉模型钉版与 effort |
| 合入 10.1.0 后未发布项 | CC/CX 包配置对齐官方文档、安装器 env 补缺、仓库整理（见 `CHANGELOG.md`） |

## 破坏性变更

| 项 | 影响 |
|---|---|
| `.ai_state` | 无。schema v2 不变；`athena migrate --to 10.1` 仍是 9.9.x → v2 的唯一迁移 |
| 黄区默认 | 由派子 agent 改为主 agent 直做；子 agent 只为隔离或并行 |
| 包内默认 | CC `settings.json` 去 `effortLevel`；Codex `config.toml` 去 `model` / `model_reasoning_effort` / `plan_mode_reasoning_effort`。已装用户的配置不受影响（安装器合并、用户优先），新装走平台默认 |

## 发布门

| 门项 | 结果 |
|---|---|
| fixture | 通过：Mac 对 Claude 候选 3552697 全量 329 项零跳过，`athena run` 证据 260bb9180af0；发布说明更新后的最终证据见本轮归档 |
| 安装 / 回滚演练 | 通过：两轮真机 `install --platform cc,cx` → doctor 无 drift → rollback 恢复 10.1.0；第二轮 238 个管理路径的内容/权限均回到该轮基线。第一轮运行窗口的四个 Claude 配置字段变化与原始备份均保留，见 Mac 发布门报告 |
| 探针 P8 | 通过：CC 2.1.289 原生 Quick→ship；补充现成 sprint 启动确认非空 JSON 上下文被接收，52 个 hook 响应均成功，无序列化误拦。两个原生会话与测试项目保留 |
| 探针 P1–P7 | 顺延下一版（插件 / Pi 原生事件）：CC 清单与组件发现、CX 临时安装与原生加载已跑，见 `.ai_state/roadmap/athena-10-1-5/probes.md` |
| 插件清单 | experimental，不阻塞：CC 2.1.289 validate 通过；CX 0.160.0 不带 `$schema` 时发现 22 skills / 8 hooks；带 `$schema` 时 0 hooks 是上游 openai/codex#47925 |
| 行为评测 | 未跑，不阻塞本版：D-014 去向为 10.2 发布门 |
| Pi 扩展 | 本机两个扩展对 Pi 1.0.2 类型检查通过（TypeScript 7.0.2，临时环境）；真实 Pi 事件链顺延 |

Mac 运行记录与清理边界：`.ai_state/docs/reports/2026-10-05-athena-10-1-5-mac-release-gates.md`。已清理上轮 Pi 检查的可再生临时依赖，保留原始配置备份、回滚事务与会话历史。

## 已知限制

- 插件壳为 experimental：模板已改用随包 `gate/templates/`，CC agents 优先随包 CLI；rules / 全局配置仍按设计由安装器提供。
- U-001：CX 根清单故意不带 Agent Plugins `$schema`。带上后 Codex（≤0.160.0 实测）按 AgentPlugin 格式加载、整段跳过 hooks（openai/codex#47925，未修）；不带时按默认 `hooks/hooks.json` 发现，hooks 不缺，只是根清单 description 不被读取。上游修复后再加。
- 同一平台不要同时启用安装器形态与插件形态：每道门跑两遍（`doctor` 报 WARN）。
- Codex code mode、`spawn_agent` 是否触发 PreToolUse：官方 hooks 文档已写明两者都触发，仍待实测（P1/P2）；未触发则 H1/H4 在 CX 降级。
- 只有插件形态时 `doctor` 只报 WARN 与缺什么，不代为安装；补安装器部分前先停用同端插件 hooks。
- Stop 连续三次同因拦截后仍熔断放行，并写入 `issues.md`。

## 回滚

| 回滚什么 | 怎么做 |
|---|---|
| 本机安装 | `athena rollback`（回到上次安装前；装过 10.1.0 即回 10.1.0） |
| 插件形态 | 停用 / 卸载插件（`claude plugin` 或 Codex 插件管理）；不碰 `~/.athena` |
| 项目 `.ai_state` | 无需：本版不改状态 |
| 源码 | 10.1.0 = `f4af800`（tag `v10.1.0`，本克隆未取到）；10.1.5 基线 `1c1cd73` |

---

## 历史：10.1.0 发布声明

| 项 | 值 |
|---|---|
| 版本 | 10.1.0（minor，基线 9.9.9） |
| 日期 | 2026-09-24 |
| Tag | `v10.1.0` → `f4af800` |
| 部署范围 | Claude Code + Codex；Pi 构建与测试覆盖，默认不部署 |

一句话：9.9.x 是「三端各一套 hook + 长宪法劝导」，10.1 改成「一个 JS 门禁核机械强制 + 一个 `athena` CLI 记账 + 一份短宪法」。

| 项 | 内容 |
|---|---|
| 单源构建 | `vibeCoding/athena/` → `dist/{claude,codex,pi,athena}`；版本号只来自 `VERSION` |
| 门禁核 | `~/.athena/current/hook.cjs`，三端同一套规则：H1 design-first、H2 证据、H3 review、H4 红区隔离、H5 shell；提示项 A1–A10 |
| 证据 | `athena run [--covers ACn] -- <cmd>`，绑定源码树 sha；手写证据不再被读取 |
| review | `athena review prepare` → 独立 reviewer → `athena review accept` |
| 状态 v2 | `_index.md` 路由器 ≤3 KB；sprint = design + log (+ review.json)；`issues.md` 单一问题账；按月归档 |
| 安装器 | `athena install / doctor / rollback`，事务式、合并不覆盖 |
| 提示词 v2 | 宪法三端同源 1.6 KB；rules ~140 行；skills 单源 |

破坏性变更：项目 `.ai_state` 需迁移（`athena migrate --to 10.1`）；9.9.x 的 hook、`setup-athena.py`、`athena-migrate`、critic / evaluator / spec-compliance 等全部退役；证据只认 `athena run`。

| 发布门 | 结果 |
|---|---|
| fixture 三端全绿 | 通过（发布时 156/156） |
| 行为评测对 9.9.9 不退化 | **豁免**：`.ai_state/decisions/2026-09-24-decision-athena-10-1-release-gate.md`；债务 D-014，10.2 恢复 |
| Rlues + quantum-agent 迁移 | dry-run 通过（Blockers 0），两仓均已实迁 |
| 安装 / 回滚演练 | fixture 逐字节回滚验证；真机 dry-run → install → `doctor: no drift` |
| quantum 真实 Feature sprint | major 条件，10.1 不适用；发布后验证 |

已知限制（10.1.0 时）：无质量不退化的量化证据；Pi 以 followUp 代替 Stop 硬停（10.1.5 已做）；Stop 三连拦熔断；`~/.claude/settings.json` 里旧版遗留的无效插件键不被安装器清理。

回滚（10.1.0）：本机 `athena rollback`；项目 `.ai_state` 回 tag `pre-athena-10.1-state`（仅状态迁移，见 `MIGRATION.md` §5）；10.1 之前的源码 `d42979a`（10.1 合入点 `cfc76aa`）。
