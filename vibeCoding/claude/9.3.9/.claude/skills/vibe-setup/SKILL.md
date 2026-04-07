---
name: vibe-setup
disable-model-invocation: true
description: >
  VibeCoding 安装向导。安装插件、初始化项目。首次使用时运行。
---

# /vibe-setup — 安装和初始化

## 环境检测
!`claude --version 2>/dev/null | head -1 || echo 'CC 版本未知'`
!`command -v codex >/dev/null 2>&1 && echo "✅ codex CLI" || echo "❌ codex CLI 未安装"`
!`npx ctx7 --version 2>/dev/null && echo "✅ context7" || echo "❌ context7 未安装"`
!`npx ecc-agentshield --version 2>/dev/null && echo "✅ ECC AgentShield" || echo "❌ ECC 未安装"`

## 安装插件 (如需要)

```bash
# superpowers
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# codex-plugin-cc
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex

# ECC
/plugin marketplace add affaan-m/everything-claude-code
/plugin install everything-claude-code@everything-claude-code

# context7
/plugin marketplace add upstash/context7
/plugin install context7-plugin@context7-marketplace

# 重新加载
/reload-plugins
```

## 初始化项目

```bash
mkdir -p .ai_state
# 从 skill templates 复制
```

复制 riper-pace/templates/ 下所有模板到 .ai_state/。

如果项目有 .gitignore → 建议添加 `.ai_state/`

## 验证

- `/codex:review` → 应能执行
- `npx ctx7 resolve express` → 应输出文档
- `npx ecc-agentshield scan` → 应输出报告
- 说 "帮我分析需求" → superpowers brainstorming 应激活
