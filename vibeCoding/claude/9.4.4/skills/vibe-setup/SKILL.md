---
name: vibe-setup
disable-model-invocation: true
description: >
  VibeCoding 全局安装。检查 CC 版本、装插件、装 Gstack、装 context7 skill、配置 Codex、部署 hooks。首次使用运行一次。
---

# /vibe-setup

## Step 0: CC 版本检查

```bash
claude --version
```

要求 v2.1.111 或更高 (Opus 4.7 最低要求)。低于 → `claude update` 或 `npm install -g @anthropic-ai/claude-code@latest`。

## Step 1: Gstack 安装

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup
```

安装后确认 /office-hours 可用。

## Step 2: 插件安装 (CC 原生)

逐个安装，跳过已有的:

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex

/plugin marketplace add lackeyjb/playwright-skill
/plugin install playwright-skill@playwright-skill

/reload-plugins
```

官方插件 (claude-plugins-official 已内置):

```
/plugin install feature-dev
/plugin install code-review
/plugin install commit-commands
/plugin install security-guidance
/plugin install frontend-design
```

## Step 3: context7 安装 (skill 模式，非 plugin)

```bash
npx ctx7 setup --claude
```

无需全局安装 ctx7 CLI，npx 会按需拉取。OAuth 登录后会自动在 `~/.claude/skills/` 下生成 context7 skill。
触发方式: "use context7" 或 "use context7 with /owner/repo for <query>"。
Skill 内部指示 agent 跑 `ctx7 library <n>` 和 `ctx7 docs <id>`，这些命令会通过 npx 解析。

## Step 4: Codex 配置 (关键)

```
/codex:setup
```

检查 Codex CLI 已安装 + 登录。未登录:

```
!codex login
```

**不要启用 review gate** (`/codex:setup --enable-review-gate`)——会造成 Claude ↔ Codex 死循环，快速耗尽配额。VibeCoding 通过 `/codex:review` 显式调用已足够。

Codex 用独立配置 `~/.codex/config.toml` 或项目级 `.codex/config.toml`。省钱推荐 rescue 任务用 `gpt-5.4-mini`:

```toml
# ~/.codex/config.toml
model = "gpt-5.4-mini"
model_reasoning_effort = "high"
```

## Step 5: Hooks 安装

```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/*.cjs ~/.claude/hooks/
```

`/hooks` 确认 5 个 hook:
PreToolUse · Stop · PermissionDenied · PreCompact · PostCompact

## Step 6: 验证

```bash
ls ~/.claude/skills/gstack/SKILL.md        # Gstack
ls ~/.claude/skills/context7*               # context7 skill
npx ctx7 library express                    # context7 CLI 通
/plugin list                                # 确认 codex / superpowers 已装
npx ecc-agentshield --version               # ECC (npx 调用, 无需 plugin)
/codex:setup                                # Codex 端 ready
```

通过 → "安装完成。每个新项目 `/vibe-init`，然后 `/vibe-dev`。"
