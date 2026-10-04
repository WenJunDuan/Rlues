---
roadmap_slug: athena-10-5
created: "2026-10-04"
status: in_progress
author: claude (cowork, fable-5.1)
reviewer: 待定（计划 codex gpt-6.1-sol）
---
# Athena 10.5 设计 — 「插件就绪」

> 情报与取舍全文：项目文档 `claude/athena-10.5-iteration-plan.md`；情报快照：`.ai_state/docs/research/2026-10-04-radar.md`。
> 基线 `1c1cd73`（VERSION 10.1.0 + 26 提交）。分支 `athena-10.5`。

## 0. 定位

| 版本 | 内容 |
|---|---|
| 10.5（本版） | 三端各出可装的插件壳（门禁核仍是同一个 `hook.cjs`）+ 实撞 MUST + 提示词 v3 + Pi 硬 Stop |
| 下一版 | CC 门禁迁入 mod function hooks + 三端上架。做到 = 用户定的新版本号；做不到切内核 = 10.6 |

不变量：H1–H5 语义、`.ai_state` schema v2、`athena run` 的可证明边界、证据绑树 sha、一轮审查 → 消解 → 最小复核。

## 1. 结构

### 1.1 构建产物（`build.mjs` 新增三项，旧产物保留）

```
dist/
  athena/<ver>/                 门禁核 + CLI（不变）
  claude/<ver>/.claude/         安装器形态（不变；rules、CLAUDE.md 只有它能带）
  codex/<ver>/.codex/           安装器形态（不变；config.toml、AGENTS.md 只有它能带）
  pi/<ver>/plugin/              Pi 包（已是 package.json#pi；本版改版本与 peer）
  claude-plugin/<ver>/          新增  CC 插件
    .claude-plugin/plugin.json      name=athena, version=<VERSION>
    hooks/hooks.json                command hooks → node ${CLAUDE_PLUGIN_ROOT}/gate/hook.cjs <Event> --platform cc
    gate/                           门禁核全量（vendored，与 dist/athena 同字节）
    bin/athena                      → gate/cli.cjs（插件 bin/ 进 PATH）
    skills/  agents/                与安装器形态同源
  codex-plugin/<ver>/           新增  Codex 插件
    plugin.json                     Agent Plugins schema；extensions.com.openai.hooks = ./hooks/hooks.json
    hooks/hooks.json                command hooks → node ${PLUGIN_ROOT}/gate/hook.cjs <Event> --platform cx
    gate/  skills/
```

两种形态并存：插件壳自带门禁核，不依赖 `~/.athena/current`；安装器形态继续负责插件带不走的部分。`athena doctor` 分别报告。

### 1.2 插件带不走什么（事实来源见 radar；本机未验证的标待验证）

| 端 | 带不走 | 10.5 处置 |
|---|---|---|
| CC | CLAUDE.md、path-scoped rules | 宪法由 SessionStart hook 注入（插件内 `gate/constitution.md`）；rules 留安装器 |
| Codex | `config.toml`、AGENTS.md；agents 能否随插件分发待验证 | 留安装器；插件 hook 装后须在 `/hooks` 受信 |
| Pi | 无 | 包即全部 |

### 1.3 门禁核改动点

| 文件 | 改动 | 切片 |
|---|---|---|
| `gate/rules/h1-design.cjs` + `gate/lib/context.cjs` | `.ai_state` 排除按「任一已登记 worktree 根」判（G-018 根因：嵌套 worktree 的 `<wt>/.ai_state` 相对 mainRoot 被算实现写入） | S1 |
| `gate/cli/run.cjs` | unprovable 时 stderr 末尾打印可证明写法模板；`--rebind` 对当前树重跑最后一条 typecheck/test 证据 | S1 |
| `gate/cli/review.cjs` | 拒收时打印修正样例行与下一步命令 | S1 |
| `gate/cli/issue.cjs` | `--type gate` 追加一行到配置的上游 FEEDBACK（`ATHENA_FEEDBACK` 或 `~/.athena/config.json`），缺配置不失败 | S1 |
| `gate/cli/status.cjs` | AC 覆盖矩阵 + ship 预检（缺哪条证据、H2/H3 现在会拦什么；10.1 代码里没有轻门禁，故不报） | S2 |
| `gate/cli/writer.cjs`（新） | `dispatch` 建 worktree、记 `external-writer.json`、置 `parallel_writers`；`collect` 做 merge-tree 探冲突、ff、还原 `parallel_writers`、提示复跑 | S2 |
| `gate/platform/pi.cjs` + `athena-gates.ts` | `agent_before_settle` 返回 `continue: true` 实现 H2/H3 硬停；防循环守卫；peer 放宽到 1.x | S4 |
| `gate/core.cjs` | SessionStart 注入支持「宪法全文」（仅插件形态，由环境变量指明路径） | S3 |
| `gate/cli/doctor.cjs` | 报告插件形态 / 安装器形态各自状态 | S3 |

### 1.4 提示词 v3（S5）

| 文件 | 改动 | 出处 |
|---|---|---|
| `core/package/AGENTS.md` | 「完成」条换成点名早停形态 + 末段自检；加「范围即交付物」；例行 athena 命令显式授权；进度更新一句 | Anthropic Fable 5.1 / Opus 5.5 指南、OpenAI GPT-6 指南 |
| `rules/coding.md` | 加「删除优于兼容」「新增依赖先查已有」；测试政策按路径；P0 的行数/常量条降 P1（与反过度工程冲突，9.9.9 终审 G 项遗留） | 推上 CLAUDE.md 裁决；9.9.9 review |
| `rules/docs.md` | 临时方案写移除条件 | 同上 |
| `pace/references/execution.md` + `stages.yaml` | 黄区默认主 agent 直做；子 agent 只为隔离或并行 | Superpowers 6.4；Marmelab [二手] |
| `pace/references/platform.md` | Pi 硬停、插件形态、code mode 行、待验证项 | radar |
| `adapters/cx/package/config.toml`、`adapters/cc/package/settings.json` | 去模型钉版与写死的 effort（用户配置优先本就成立，这里去掉包内默认） | Opus 5.5 迁移指南；Codex 0.159.1 默认模型已变 |
| `core/rules.md` | 每条新规则一行出处 | 既有约定 |

原计划的「按家族宪法变体」取消：四处改动对三端都成立，一份正文即可；`test_prompts.py` 的三端同文断言保留。

## 2. 切片与写集

| 切片 | 路径 | 写集 | 依赖 |
|---|---|---|---|
| S1 gate-fixes | Bugfix+Feature | `gate/rules/h1-design.cjs` `gate/lib/context.cjs` `gate/cli/{run,review,issue}.cjs` `gate/lib/evidence.cjs` + 新 fixture | — |
| S2 status-writer | Feature | `gate/cli/{status,writer}.cjs` + 新 fixture | — |
| S3 plugin-shells | System | `build.mjs` `adapters/{cc,cx}/plugin/**` `adapters/*/platform.json` `gate/core.cjs`(注入) `gate/cli/doctor.cjs` `evals/fixtures/test_build.py` + 新 fixture | — |
| S4 pi-hard-stop | Feature | `adapters/pi/top/plugin/**` `gate/platform/pi.cjs` + 新 fixture | — |
| S5 prompts-v3 | Feature | `core/package/**` `core/rules.md` `core/pace/stages.yaml` `adapters/{cc,cx}/package/{settings.json,config.toml}` `evals/fixtures/test_prompts.py` | S3 合入后改 platform.md |
| S6 probes-eval | — | 需本机 CC / Codex / Pi CLI，云端做不了；步骤见 `probes.md` | S3、S4 |
| S7 release | System | `VERSION` `RELEASE.md` `CHANGELOG`、tag、装机 | 全部；不可逆，用户确认 |

公共文件（`gate/cli.cjs` USAGE、`VERSION`、本目录）只由主会话写。

## 3. 验收

| AC | 内容 | 证据 |
|---|---|---|
| AC1 | 嵌套 worktree 内写 `<wt>/.ai_state/sprints/<s>/design.md` 放行；同 worktree 内写源码在无 AC 时仍拦 | 新 fixture |
| AC2 | `athena run` 不可证明、`review accept` 拒收、covers 格式错：stderr 含可复制的修正样例 | 新 fixture |
| AC3 | `athena run --rebind` 在当前树重跑最后一条 test/typecheck 证据并记新 tree_sha；重跑失败不记 PASS | 新 fixture |
| AC4 | `athena status` 输出每条 AC 的证据状态与 ship 预检结论 | 新 fixture |
| AC5 | `athena writer dispatch` 建 worktree + `external-writer.json` + `parallel_writers≥2`；`collect` 探冲突并还原 | 新 fixture |
| AC6 | `build.mjs` 产出 `claude-plugin`、`codex-plugin`，manifest 版本 = VERSION，hooks 指向插件根，门禁核与 `dist/athena` 同字节 | `test_build.py` |
| AC7 | Pi 适配：stop 被拦时 render 返回 `{continue:true}` 形态所需字段；同因重复有上限 | 新 fixture（适配层；扩展 .ts 无法在此实跑） |
| AC8 | 宪法 ≤2.5 KB、三端同文、无「仔细思考 / 输出推理过程」类指令；新规则在 `core/rules.md` 有出处行 | `test_prompts.py` |
| AC9 | 既有 fixture 不退化（基线：本环境 233 过 / 2 败，2 败为环境相关的 npm/HOME 用例） | 全量 pytest |
| AC10 | P1–P5 探针结论写入 `platform.md` | S6，待本机 |

## 4. 风险

| 风险 | 处置 |
|---|---|
| CC / Codex 插件 manifest 字段取自官方文档的转述，未在本机 `claude plugin validate` / Codex 安装验证 | S6 探针 P4/P6；RELEASE 标待验证 |
| Pi 扩展 `.ts` 在此环境无法加载实跑 | 逻辑下沉到 `pi.cjs`（可测），扩展只做薄转发；S6 实跑 |
| `agent_before_settle` 返回值字段名取自 Pi 仓库文档 | 同上 |
| writer collect 涉及 git 合并 | 只做 `merge-tree` 探测 + `--ff-only`；有冲突即停，不自动解 |
