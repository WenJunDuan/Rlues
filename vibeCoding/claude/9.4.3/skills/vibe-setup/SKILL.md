---
name: vibe-setup
disable-model-invocation: true
description: >
  VibeCoding 全局安装。安装插件、Gstack 和 hooks。首次使用运行一次。
---

# /vibe-setup

## Step 1: Gstack 安装

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup
```

安装后确认 /office-hours 可用。

## Step 2: 插件安装

逐个安装，跳过已有的:

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex

/plugin marketplace add upstash/context7
/plugin install context7-plugin@context7-marketplace

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

## Step 3: Hooks 安装

```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/*.cjs ~/.claude/hooks/
```

`/hooks` 确认 5 个 hook:
PreToolUse · Stop · PermissionDenied · PreCompact · PostCompact

## Step 4: 验证

```bash
ls ~/.claude/skills/gstack/SKILL.md  # Gstack
ctx7 library express                  # context7
/plugin list                          # 确认 codex 插件已安装
npx ecc-agentshield --version         # ECC (npx调用, 无需plugin)
```

通过 → "安装完成。每个新项目 `/vibe-init`，然后 `/vibe-dev`。"
