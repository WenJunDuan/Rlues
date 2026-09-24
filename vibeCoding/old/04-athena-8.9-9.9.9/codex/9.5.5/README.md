# VibeCoding Hermes Kernel — Codex 端 v9.5

> Codex 做事，Hermes 把关。AI 工程纪律的 context engineering 配方。

## 这是什么

Hermes 不是 framework，是一套约束 + 提示 + 状态文件，让 Codex 按工程纪律工作：

- **PACE 路由器** — 按任务复杂度选 6 条路径之一
- **铁律 7 条** — 设计先行 / TDD / Sisyphus / Review / 文档即真相 / 完成度证据 / 出处优先
- **`.ai_state/` 状态文件** — Anthropic 推荐的 structured note-taking pattern（与 CC 端 schema 一致）
- **Hook 守卫** — 6 个 Python hook 覆盖 6 个事件，softhook 为主，硬阻断仅 3 条灾难命令

## Quick Start

```bash
# 1. 解压到 ~/.codex
unzip vibecoding-hermes-v95-codex.zip -C ~

# 2. 让 Codex 读到
chmod +x ~/.codex/hooks/*.py

# 3. 验证
codex --version                         # 需 ≥ v0.124.0
ls ~/.codex/hooks/*.py                  # 应有 6 个文件
grep VIBECODING_VERSION ~/.codex/config.toml  # 应为 9.5-codex
cat ~/.codex/AGENTS.md                  # 看 7 条铁律

# 4. 第一次用
codex
> /vibe-setup                           # 全局安装
> /vibe-init                            # 进入项目目录初始化 .ai_state/
> /vibe-dev "需求描述"                   # 开干
```

## Codex 平台优势（v9.5 文档化）

| 维度 | Codex | CC |
|------|-------|-----|
| Terminal-Bench | 77.3% | 65.4% |
| Token 消耗（同任务）| 0.25-0.33× | 1.0× |
| 插件市场 | 90+（3/27/2026 上线）| 100+ |
| 设计/架构判断 | 略弱 | Opus 4.7 略强 |

**v9.5 路由建议**：终端密集任务、大量重复改写 → 走 Codex。设计/架构判断 → CC 主跑。

## 我们做什么 / 不做什么

**做**：路由、状态管理、质量门、失败处理协议、防伪装。
**不做**：跨项目知识管理（装 superpowers）、重新发明插件、反 LLM 偏见硬约束。

## PACE 节点 best-fit（Codex 端）

| 节点 | 推荐 |
|------|------|
| Quick / Feature | superpowers / context7 |
| 集成类 | Slack / Linear / Notion / Figma / GitHub plugins (Codex marketplace) |
| 跨项目记忆 | superpowers `/using-superpowers` |
| 自建技能 | `@plugin-creator` 内置 scaffold |

## 故障排查

| 症状 | 解决 |
|------|------|
| `codex_hooks` not enabled | `codex features enable codex_hooks` |
| spawn_agent 找不到 reviewer | 检查 `~/.codex/agents/reviewer/AGENTS.md` 存在 |
| Stop hook 一直阻断 | 检查 `.ai_state/reviews/sprint-N.md` VERDICT 字段 |
| sandbox 拦截测试命令 | `~/.codex/config.toml` 调 `sandbox_mode = "workspace-write"` |
| pre-bash-guard 误拦 | v9.5 仅 3 条灾难命令 |

## 设计哲学

参见 [AGENTS.md](.codex/AGENTS.md)（constitution）和 [skills/pace/SKILL.md](.codex/skills/pace/SKILL.md)（路由器）。

参考 [Anthropic effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)。

## 协议

`.ai_state/` schema 与 CC 端 v9.5 一致。项目可以在 CC / Codex 之间切换不丢状态。

完整 RELEASE-NOTES 见 [.codex/RELEASE-NOTES.md](.codex/RELEASE-NOTES.md)。
