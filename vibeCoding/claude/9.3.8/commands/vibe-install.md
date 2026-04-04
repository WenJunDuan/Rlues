# /vibe-install — 安装 VibeCoding 插件栈

一键安装所有 VibeCoding 依赖的插件和工具。首次使用时运行一次。

## 安装步骤

依次执行以下命令 (如已安装会自动跳过):

```bash
# 1. 添加插件市场源
/plugin marketplace add openai/codex-plugin-cc
/plugin marketplace add obra/superpowers-marketplace
/plugin marketplace add affaan-m/everything-claude-code
/plugin marketplace add lackeyjb/playwright-skill
/plugin marketplace add upstash/context7

# 2. 安装插件
/plugin install codex@openai-codex
/plugin install superpowers@superpowers-marketplace
/plugin install everything-claude-code@everything-claude-code
/plugin install playwright-skill@playwright-skill
/plugin install context7-plugin@context7-marketplace

# 3. 检查 Codex CLI
/codex:setup
# 如果 Codex 未安装, /codex:setup 会提示安装
# 如果未登录: !codex login

# 4. 检查 context7
npx ctx7 --version

# 5. 检查 ECC AgentShield
npx ecc-agentshield --version

# 6. 重新加载插件
/reload-plugins
```

## 验证

安装完成后, 确认以下功能可用:
- `/codex:review` → Codex 审查 (输入后应看到审查输出)
- `/codex:rescue test` → Codex 委托 (应启动任务)
- 说 "帮我分析一下需求" → superpowers brainstorming skill 应自动激活
- `npx ctx7 resolve express` → 应输出 Express 库文档
- `npx ecc-agentshield scan` → 应输出安全扫描报告

全部可用 → 告知用户: "VibeCoding 插件栈安装完成。用 /vibe-init 初始化项目, 或 /vibe-dev 开始开发。"
