# VibeCoding Athena v9.6.1

> **"CC 做事, Athena 把关"** — 双平台 (Claude Code + Codex CLI) AI 编码工程化框架.

## v9.6.1 一句话总结

v9.6 的 **patch 级修订**: 1) 清洗 cx config.toml 私有数据 (P0 安全); 2) 把 Codex /goal 从"无"修正为 v0.128.0+ GA (P1 全链 8 文件); 3) 接入 v9.7 真金 4 行宪法 (R10/R11/R12 + META-0).

不增模块、不动 schema、不破 dogfood 数据收集.

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
# Codex 重启 (要求 ≥ v0.124, 期望 ≥ v0.128 解锁 /goal)
/athena-setup       # 装配置, 检测 Codex 版本
/athena-init        # 每个新项目
/athena-dev <需求>  # 开干
```

## 文档地图

| 文件                                           | 给谁看                              |
| ---------------------------------------------- | ----------------------------------- |
| `cc/.claude/CLAUDE.md` / `cx/.codex/AGENTS.md` | **AI 自己** (宪法, ≤35 行)          |
| `cc/.claude/skills/pace/SKILL.md`              | AI 自己 (PACE 路由 + 流程)          |
| `cc/.claude/skills/athena-*/SKILL.md`          | AI 自己 (各个 athena-\* 命令的实现) |
| `cc/.claude/hooks/*.cjs`                       | 系统 (在 lifecycle 触发)            |
| `cc/.claude/settings.json`                     | CC 配置, 严格按官方 schema          |
| `cx/.codex/config.toml`                        | Codex 配置, 严格按官方 schema       |
| **README.md** (本文件)                         | 给你看 (快速上手)                   |
| **RELEASE-NOTES.md**                           | 给你看 (v9.6 → v9.6.1 变更)         |
| **iterate-checklist.md**                       | 给下次迭代的你自己 (研究先行 SOP)   |

## v9.6.1 改动 (vs v9.6.0)

### 修
- **P0 安全**: `cx/.codex/config.toml` 删除真实 ACE token / 用户 workspace 路径 / hooks.state 信任哈希; 改为占位符 + 注释说明
- **P1 Codex /goal**: 8 处描述/检测逻辑修正 (rust-v0.128.0 GA, 2026-04-30)
  - AGENTS.md / skills/pace/SKILL.md / skills/pace/context-essentials.md
  - hooks/session-start.py (删 "(CC only)")
  - prompts/{athena-init,athena-setup,athena-status,athena-review}.md
  - skills/pace/templates/goal-conditions.md (加 Codex 端段)
- **P3 一致性**: `cc athena-setup` Step 4 "hook 列表 (8 个)" → 实际 10 个; `cx pre-bash-guard.py` 正则与 CC 端对齐

### 加 (来自 v9.7 真金, 仅 4 行宪法精炼)
- **铁律 10 校准报告**: 关键声明附 `executed` / `inspected` / `assumed` 标签
- **铁律 11 可逆性加权**: 跨边界 (生产/schema/API) 必须 `executed` 证明
- **铁律 12 矛盾不折中**: 竞争方案二选一, 命名被弃方案
- **META-0** (入 `<important>` 段末句): 第一性分析与铁律冲突 → 命名编号 + 给理由继续推进

### 不动
- PACE 6 路径定义 / `.ai_state/` schema (仍 9.6) / 文件总数 / hook 总数 / 插件清单

## 平台支持矩阵 (v9.6.1 已对齐)

| 功能                                  | CC                       | Codex                             |
| ------------------------------------- | ------------------------ | --------------------------------- |
| PACE 6 路径路由                       | ✓                        | ✓                                 |
| `.ai_state/` schema 9.6               | ✓                        | ✓ (跨平台 parity, 铁律 6)         |
| `/athena-init/dev/review/...`         | ✓                        | ✓                                 |
| `/athena-preferences` 全局 allow/deny | ✓                        | 部分 (Codex 用 approval_policy)   |
| **`/goal` autonomous loop**           | **✓ v2.1.139+**          | **✓ v0.128.0+ GA (新对齐)**       |
| `/batch` 并行 worktree                | ✓ v2.1.121+              | ✗ (spawn_agent 多线程, 无 worktree 隔离) |
| `/background` 多会话                  | ✓ v2.1.139+              | ✗                                 |
| compact 生命周期                      | ✓ PreCompact/PostCompact | ✗                                 |
| Cross-session memory                  | ✓ (claude-mem 推荐)      | ✗ (人工同步 AGENTS.md)            |
| Hooks Windows 支持                    | ✓                        | ✗ (官方限制)                      |

## 配置参考链接

### Claude Code

- [Settings](https://code.claude.com/docs/en/settings)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Permissions](https://code.claude.com/docs/en/permissions)
- [Plugins](https://code.claude.com/docs/en/plugins)
- [Skills](https://code.claude.com/docs/en/skills)
- [Goal](https://code.claude.com/docs/en/goal)

### Codex CLI

- [Config Basics](https://developers.openai.com/codex/config-basic)
- [Config Reference](https://developers.openai.com/codex/config-reference)
- [Advanced Config](https://developers.openai.com/codex/config-advanced)
- [Hooks](https://developers.openai.com/codex/hooks)
- [Changelog](https://developers.openai.com/codex/changelog) ← v0.128.0 /goal GA
- [GitHub release rust-v0.128.0](https://github.com/openai/codex/releases/tag/rust-v0.128.0)

### 设计参考

- Anthropic [Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Anthropic [Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)
