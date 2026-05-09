# VibeCoding Hermes Kernel — Claude Code 端 v9.5

> CC 做事，Hermes 把关。AI 工程纪律的 context engineering 配方。

## 这是什么

Hermes 不是 framework，是一套约束 + 提示 + 状态文件，让 Claude Code 按工程纪律工作：

- **PACE 路由器** — 按任务复杂度选 6 条路径之一（Hotfix/Bugfix/Quick/Feature/Refactor/System）
- **铁律 7 条** — 设计先行 / TDD / Sisyphus / Review / 文档即真相 / 完成度证据 / 出处优先
- **`.ai_state/` 状态文件** — Anthropic 推荐的 structured note-taking pattern
- **Hook 守卫** — 10 个 hook 覆盖 9 个事件，softhook 为主，硬阻断仅 3 条灾难命令

## Quick Start

```bash
# 1. 解压到 ~/.claude
unzip vibecoding-hermes-v95-claude-code.zip -C ~

# 2. 让 Claude 读到
chmod +x ~/.claude/hooks/*.cjs

# 3. 验证
claude --version              # 需 ≥ v2.1.121
ls ~/.claude/hooks/*.cjs       # 应有 10 个文件
cat ~/.claude/CLAUDE.md        # 看 7 条铁律

# 4. 第一次用
claude
> /vibe-setup                  # 全局安装（装 superpowers / codex / context7 等）
> /vibe-init                   # 进入项目目录后初始化 .ai_state/
> /vibe-dev "需求描述"          # 开干
```

## 我们做什么

- 路由（决定走哪条路径，走完整流程还是直接干）
- 状态管理（`.ai_state/` 让中断 + 恢复 + 跨 session 不丢上下文）
- 质量门（delivery-gate 在 review 阶段卡 VERDICT）
- 失败处理协议（工具失败 3 轮重试 + 完整 stderr 取证）
- 防伪装（铁律 6：完成度证据 = tool_use ID 或命令输出片段）

## 我们不做什么

- 跨项目知识管理 — 装 [claude-mem](https://github.com/AnyResearch/claude-mem) 或 superpowers
- 重新发明 plugin / IDE / VCS — 直接接入 superpowers / codex-plugin-cc / context7
- 反 LLM 偏见的硬约束 — 改用正向证据要求 + just-in-time 注入
- Web UI / 服务端 — 都在你本地的 ~/.claude/ 里跑

## PACE 节点 best-fit 插件

vibe-setup 会按以下表推荐，按需安装。**不强依赖**——没装也能跑。

| 路径 | 推荐 |
|------|------|
| Bugfix | debugger / bug-fix / metronome |
| Feature 实现 | superpowers / dev-workflows / context7 |
| Feature 审查 | codex-plugin-cc / agent-peer-review / local-review |
| Refactor | TypeScript LSP / Rust LSP / ast-grep |
| Refactor 审查 | codex-plugin-cc / AgentLint |
| System | shipyard (IaC) / mcp-builder |
| 跨节点 | claude-mem / context-mode / skill-bus |

## 故障排查

| 症状 | 解决 |
|------|------|
| 启动时提示 "context-essentials.md 找不到" | `cp -r .claude/skills ~/.claude/` |
| `/vibe-init` 失败 "找不到 templates" | `ls ~/.claude/skills/pace/templates/`，应有 8 个 .md/.sh/.json |
| Stop hook 一直阻断 | 检查 `.ai_state/reviews/sprint-N.md` 是否有 VERDICT 字段 |
| codex tool 报"无 Bash 权限" | settings.json 加 `Bash(codex:*)` 和 `Bash(node:*)` |
| pre-bash-guard 误拦 | v9.5 仅 3 条灾难命令；如果还撞墙说明命令是 `rm -rf /` 这种 |
| effort=max 不注入 PACE 状态 | 故意的，max effort 模型自己探索 |

## 设计哲学

参见 [CLAUDE.md](.claude/CLAUDE.md)（constitution）和 [skills/pace/SKILL.md](.claude/skills/pace/SKILL.md)（路由器）。

参考 [Anthropic effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)。

## 协议

`.ai_state/` schema 与 Codex 端 v9.5 一致——项目可以在 CC / Codex 之间切换不丢状态。

完整 RELEASE-NOTES 见 [.claude/RELEASE-NOTES.md](.claude/RELEASE-NOTES.md)。
