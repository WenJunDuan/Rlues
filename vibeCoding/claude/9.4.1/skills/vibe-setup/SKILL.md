---
name: vibe-setup
disable-model-invocation: true
description: >
  VibeCoding 全局安装。安装插件和 hooks。首次使用运行一次。
---

# /vibe-setup

## 插件

逐个安装，跳过已安装的:

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex

/plugin marketplace add affaan-m/everything-claude-code
/plugin install everything-claude-code@everything-claude-code

/plugin marketplace add upstash/context7
/plugin install context7-plugin@context7-marketplace

/plugin marketplace add lackeyjb/playwright-skill
/plugin install playwright-skill@playwright-skill

/reload-plugins
```

## Hooks

```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/*.cjs ~/.claude/hooks/
```

`/hooks` 确认 5 个 hook 加载:
PreToolUse · Stop · PermissionDenied · PreCompact · PostCompact

## 验证

```bash
ctx7 library express
npx ecc-agentshield --version
which codex
```

通过 → "安装完成。每个新项目用 `/vibe-init`，然后 `/vibe-dev` 开始。"
