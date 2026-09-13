# Athena · Pi 端

无版本目录。始终 at least 当前 `vibeCoding/claude/` 最新结构（现 9.9.9）。
官方：[earendil-works/pi](https://github.com/earendil-works/pi)（104k）。文档用 `gh api` 读 `packages/coding-agent/docs/`。

## 默认加载

本仓扩展：

| 文件 | 作用 |
|---|---|
| `extensions/athena-gates.ts` | bash/write → cc-core 门禁；`agent_end` followUp（Pi 无硬 Stop） |
| `extensions/athena-lifecycle.ts` | session 注入、面包屑、compact |
| `extensions/cc-core/` | 被上面调用的 hook 逻辑 |

外部包（已写入 `settings.json` `packages`）。来源：[Chasen Harness](https://x.com/chasen_liao/status/2092963119337476137) + [上下文四闸](https://x.com/chasen_liao/status/2099066585675862280)。

| 包 | 作用 |
|---|---|
| `npm:pi-subagents` | 黄/红区；scout/worker/reviewer 独立 context |
| `npm:pi-skillful` | skill 隐藏/`$` 展开，常驻做薄 |
| `npm:@eko24ive/pi-ask` | 歧义先问，少返工 |
| `npm:@ff-labs/pi-fff` | 换 find/grep，索引+分页，少灌原始搜索 |
| `npm:pi-web-access` | 搜网页+抽正文（DeepSeek 无原生搜索；不装 Tavily 第二套） |
| `npm:pi-context-usage` | `/context` 看烧到哪 |
| `npm:@narumitw/pi-btw` | 侧边线程，不污染主对话 |
| `npm:@narumitw/pi-goal` | 长目标闸门；不替代 PACE stage |
| `npm:pi-auto-compact` | 接近上限自动收缩 |
| `npm:context-mode` | 大日志/shell 先摘要，细节按需检索 |

```bash
pi install npm:pi-subagents npm:pi-skillful npm:@eko24ive/pi-ask \
  npm:@ff-labs/pi-fff npm:pi-web-access npm:pi-context-usage \
  npm:@narumitw/pi-btw npm:@narumitw/pi-goal npm:pi-auto-compact npm:context-mode
```

不加：`pi-guardrails`（与 athena-gates 双门禁）、pim-agent / monopi / agent-pi / pi-todo / pi-code / `@tavily/pi-extension`（已有 web-access）。

## 项目初始化

PACE 在 `skills/pace/`。项目状态在仓库 `.ai_state/`（本 harness 仓库已有；**新项目**用 `/athena-init`）。
已存在 `.ai_state` 不覆盖。非 git 先 `git init`。

## 结构

| CC | 本目录 |
|---|---|
| `CLAUDE.md` | `AGENTS.md` |
| `.claude/skills/` | `skills/`（PACE 在此） |
| `.claude/rules/` | `rules/` |
| `.claude/hooks/` | `extensions/cc-core/` + 两个适配器 |
| `.claude/agents/` | `prompts/`（`/generator` `/reviewer` `/architect` `/polish-worker`） |

红区：`git worktree` + 新 pi session。无 `isolation: worktree`。

## Hook 映射

官方事件：[extensions.md](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md)

| CC | Pi | 状态 |
|---|---|---|
| SessionStart | `session_start` | 已接 |
| breadcrumb | `before_agent_start` | 已接 |
| PreToolUse Bash | `tool_call` bash | 已接 |
| PreToolUse Edit/Write | `tool_call` edit/write | 已接 |
| Stop | `agent_end` followUp | 降级，无硬停 |
| Compact | `session_before_compact` / `session_compact` | 已接 |
| Agent/Subagent/Worktree 事件 | 无 | 不伪造；用 git worktree |

## 安装

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
pi install /绝对路径/vibeCoding/pi-agent
# 或软链 AGENTS.md settings.json models.json prompts rules skills extensions
# → ~/.pi/agent/。不要链整个目录（sessions 在那边）。
# 首次: cp auth.json.example ~/.pi/agent/auth.json && chmod 600
```

## 来源

| 源 | 取/不取 |
|---|---|
| [earendil-works/pi](https://github.com/earendil-works/pi) | 合同 |
| [badlogic/pi-skills](https://github.com/badlogic/pi-skills) | skill 目录惯例 |
| [bd-dxg/my-pi](https://github.com/bd-dxg/my-pi) | 取 models/retry；不取问卷、todo、正则门禁 |
| [ruizrica/agent-pi](https://github.com/ruizrica/agent-pi) | 不取（六模式 vs PACE） |
| CC `vibeCoding/claude/9.9.9` | 提示词与 hook 源 |
| X @DanKornas / @zhulin902 / @ryansupak | 按需装包；MCP 非核心；保持最小 |

## 下次迭代（提示词胖点）

已压：pace / athena-dev / compound 热路径。勿回潮文言文或极端省略。
仍胖：stages、gate-contracts、rules 伪加载、quantum playbook。铁律溯源不压。
