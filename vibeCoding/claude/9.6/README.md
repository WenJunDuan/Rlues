# VibeCoding Athena v9.6

> **"CC 做事, Athena 把关"** — 双平台 (Claude Code + Codex CLI) AI 编码工程化框架.

## v9.6 一句话总结

把 v9.5.5 "Hermes" 的 4 个伪自创能力 **删掉**, 把 CC 原生 `/goal /batch /background` 接进来, 把项目状态从 9 个文件压成 1 个 `.ai_state/_index.md` 单一入口.

```
v9.5.5: 9 个状态文件, 自造 spawn_agent 协议, 自造 VERDICT 解析
v9.6:   1 个 _index.md 入口, CC 原生 /goal evaluator, CC 原生 /batch 并行
```

## 安装

### Claude Code 端

```bash
cp -r cc/.claude ~/
cd <你的项目>
# CC 重启
/athena-setup       # 一次性: 装插件, 检测 CC 版本, 推 claude-mem
/athena-init        # 每个新项目: 创建 .ai_state/ v9.6 schema
/athena-dev <需求>  # 开干
```

### Codex CLI 端

```bash
cp -r cx/.codex ~/
cd <你的项目>
# Codex 重启
/athena-setup       # 装配置, 检测 Codex 版本
/athena-init        # 每个新项目
/athena-dev <需求>  # 开干
```

## 文档地图

| 文件                                           | 给谁看                              |
| ---------------------------------------------- | ----------------------------------- |
| `cc/.claude/CLAUDE.md` / `cx/.codex/AGENTS.md` | **AI 自己** (宪法, ≤30 行)          |
| `cc/.claude/skills/pace/SKILL.md`              | AI 自己 (PACE 路由 + 流程)          |
| `cc/.claude/skills/athena-*/SKILL.md`          | AI 自己 (各个 athena-\* 命令的实现) |
| `cc/.claude/hooks/*.cjs`                       | 系统 (在 lifecycle 触发)            |
| `cc/.claude/settings.json`                     | CC 配置, 严格按官方 schema          |
| `cx/.codex/config.toml`                        | Codex 配置, 严格按官方 schema       |
| **README.md** (本文件)                         | 给你看 (快速上手)                   |
| **RELEASE-NOTES.md**                           | 给你看 (v9.5.5 → v9.6 变更)         |
| **COMMUNITY-RADAR.md**                         | 给你看 (社区项目监视模板)           |
| **iterate-checklist.md**                       | 给下次迭代的你自己 (研究先行 SOP)   |

## v9.6 核心改变

### 删

- **personal-prefs-promoter** (自动监控命令频次 → 建议入全局): 隐私决定, 改为用户显式调用 `/athena:remember-*`
- **output-evidence-augmentor** (v9.5 已 disabled, 现彻底砍)
- **18→1 条 permissions.deny**: 只留 `"Bash(rm -rf *)"` 灾难兜底, 其他靠 sandbox
- **vibecoding-plugin.json 强制依赖声明**: v9.5 编造的, 官方没这要求 (官方 plugin 用 `.claude-plugin/plugin.json`)

### 改

- `.ai_state/` 重构: 9 文件 → `_index.md` + `details/` 八件套. 单一入口 (铁律 8)
- CLAUDE.md/AGENTS.md 23 → 27 行 (新增铁律 8/9)
- delivery-gate hook: 适配 block-cap=8 安全边界
- PreCompact hook: 仅快照 `_index.md` frontmatter (30 行, 而非全文件)
- 所有 SKILL.md 加 frontmatter (effort, disable-model-invocation)

### 加

- `/athena-migrate` — v9.5 → v9.6 自动迁移
- `/athena-preferences` — 操作 CC/CX 原生全局偏好 (不造私有文件)
- `index-updater.cjs` — PostToolUse, 自动更 `_index.md` counts/pointers/fingerprints
- `pace-continuator.cjs` — Stop 时写 `next.md` + `proposals.md` (铁律 9 Hook 反思)
- `state-audit.cjs` — ConfigChange 监控 `.ai_state/` 漂移
- `goal-conditions.md` — 每 stage 一个 `/goal` condition 模板 (CC v2.1.139+)
- `claude-mem` 默认推 (跨项目记忆)

## 平台支持矩阵

| 功能                                  | CC                       | Codex                             |
| ------------------------------------- | ------------------------ | --------------------------------- |
| PACE 6 路径路由                       | ✓                        | ✓                                 |
| `.ai_state/` schema                   | ✓                        | ✓ (cross-platform parity, 铁律 6) |
| `/athena-init/dev/review/...`         | ✓                        | ✓                                 |
| `/athena-preferences` 全局 allow/deny | ✓                        | 部分 (Codex 用 approval_policy)   |
| `/goal` autonomous loop               | ✓ v2.1.139+              | ✗ (delivery-gate 兜底)            |
| `/batch` 并行 worktree                | ✓ v2.1.121+              | ✗ (spawn_agent 多线程)            |
| `/background` 多会话                  | ✓ v2.1.139+              | ✗                                 |
| compact 生命周期                      | ✓ PreCompact/PostCompact | ✗                                 |
| Cross-session memory                  | ✓ (claude-mem 推荐)      | ✗                                 |
| Hooks Windows 支持                    | ✓                        | ✗ (官方限制)                      |

## 配置参考链接 (本框架严格按这些抓的, 任何字段都有出处)

### Claude Code

- [Settings](https://code.claude.com/docs/en/settings) — settings.json 完整字段
- [Hooks](https://code.claude.com/docs/en/hooks) — 27 hook 事件 schema
- [Permissions](https://code.claude.com/docs/en/permissions) — allow/deny 语法
- [Plugins](https://code.claude.com/docs/en/plugins) — plugin 体系
- [Skills](https://code.claude.com/docs/en/skills) — SKILL.md frontmatter

### Codex CLI

- [Config Basics](https://developers.openai.com/codex/config-basic) — 优先级 + features
- [Config Reference](https://developers.openai.com/codex/config-reference) — 完整字段
- [Advanced Config](https://developers.openai.com/codex/config-advanced) — inline hooks TOML
- [Hooks](https://developers.openai.com/codex/hooks) — Codex hook 体系

### 设计参考

- Anthropic [Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — 索引先行
- Anthropic [Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system) — subagent 输出预算 ≤2000
