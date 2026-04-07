---
name: vibe-setup
disable-model-invocation: true
description: >
  VibeCoding 安装向导。安装插件、初始化项目。首次使用时运行。
---

# /vibe-setup — 安装和初始化

## 第一步: 环境检测

用 Bash 工具逐个检查以下命令, 记录哪些可用:
- `claude --version`
- `which codex`
- `npx ctx7 --version`
- `npx ecc-agentshield --version`

## 第二步: 安装缺失的插件

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

## 第三步: 初始化项目

```bash
mkdir -p .ai_state/reviews
```

从 riper-pace/templates/ 复制所有模板到 .ai_state/:
- project.json
- tasks.md
- design.md
- lessons.md

如果项目有 .gitignore → 建议添加 `.ai_state/`

## 第四步: 验证

用 Bash 工具运行以下命令确认插件可用:
- `ctx7 library express` → 应返回库信息
- `npx ecc-agentshield scan` → 应输出报告

全部通过 → 告知用户: "VibeCoding 安装完成, 用 /vibe-dev 开始开发。"
