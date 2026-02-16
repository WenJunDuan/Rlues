# VibeCoding Kernel v8.5

> AI 编程协作框架 — 不替代 AI 能力, 只编排 WHEN + WHERE + HOW MUCH。并行优先, 串行兜底。

## v8.5 变更 (从 v8.3.5)

**架构重构:**
- `.knowledge/` 合并入 `.ai_state/` — 统一状态管理
- 新增 `.ai_state/requirements/` (需求文档) + `.ai_state/assets/` (UI 设计图)
- CC/Codex 完全独立, 零交叉引用
- CLAUDE.md 精简到 45L (只说 AI 不知道的)

**Claude Code 新特性:**
- `.claude/agents/` 三个持久化子代理: builder, validator, explorer (sonnet 省 token)
- SubagentStop prompt hook — 子代理完成后自动质量验证
- Agent Teams 支持 (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1)
- CLAUDE_CODE_SUBAGENT_MODEL=sonnet — 主代理 opus, 子代理 sonnet
- 4+1 Hooks: SessionStart, Stop, PostToolUse, PreToolUse, SubagentStop
- Task/WebSearch/WebFetch 权限开放

**Codex CLI 新特性 (全部启用):**
- parallel=true — Shell 命令并行执行
- collab=true — 多代理协作模式
- steer=true — 运行中注入指令
- plan_tool=true — /plan 规划工具
- shell_snapshot=true — Shell 环境快照
- unified_exec=true — 统一执行
- view_image_tool=true — 图片查看
- skills=true + rmcp_client=true — Skills + MCP
- model_reasoning_effort=xhigh, web_search=live

**2026 最佳实践:**
- Plan-First: Path B+ 强制先规划
- Block-at-Commit: PostToolUse 非阻塞, Stop 阻塞
- 并行优先: 无依赖子任务并行调度
- Security: PreToolUse 拦截危险命令 (eval/sudo/rm -rf)

## 安装

**Claude Code:**
```bash
unzip vibecoding-v85-claude-code.zip -d ./
claude
> /vibe-init
```

**Codex CLI:**
```bash
unzip vibecoding-v85-codex-cli.zip -d ./
codex
```

## 文件结构

**Claude Code:**
```
.claude/
├── CLAUDE.md (45L)
├── settings.json
├── agents/     builder.md, validator.md, explorer.md
├── hooks/      4 个 .cjs (SessionStart/Stop/PostToolUse/PreToolUse)
├── commands/   4 个 /vibe-*
├── rules/      rules.md
├── skills/     9 个 SKILL.md
├── templates/  ai-state/ (11 模板)
└── workflows/  pace.md + riper-7.md
```

**Codex CLI:**
```
AGENTS.md (54L, 含并行工作规范)
.codex/
├── config.toml (全特性开启)
├── hooks/      2 个 .cjs (手动执行)
├── skills/     9 个 SKILL.md (独立副本)
├── templates/  ai-state/ (11 模板)
└── workflows/  pace.md + riper-7.md
```
