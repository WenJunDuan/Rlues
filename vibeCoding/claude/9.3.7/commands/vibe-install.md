---
effort: low
---
# /vibe-install — 安装 VibeCoding 所需的全部外部工具

> 只需运行一次。之后用 /vibe-init 初始化项目。

## 流程

### 1. 核心插件

```bash
# GSD — spec-driven + fresh context 执行 (gsd-build/get-shit-done)
/plugin marketplace add gsd-build/get-shit-done
/plugin install gsd@gsd-build

# Codex — 跨模型写代码 + 对抗审查 (openai/codex-plugin-cc)
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/codex:setup
# 如果 Codex CLI 未安装, /codex:setup 会提示安装
# 用 !codex login 登录 ChatGPT 或 API key

# Superpowers — brainstorm + execute-plan + plan-review (obra)
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# ECC — 安全扫描 AgentShield (affaan-m)
/plugin marketplace add affaan-m/everything-claude-code
/plugin install everything-claude-code@everything-claude-code

# Playwright — E2E 测试 + 截图 (lackeyjb)
/plugin marketplace add lackeyjb/playwright-skill
/plugin install playwright-skill@playwright-skill
```

### 2. Anthropic 官方插件

已在 settings.json 的 enabledPlugins 中声明, CC 启动时会提示 trust:

```bash
# 如果没自动提示, 手动安装:
/plugin install feature-dev@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
```

### 3. MCP 工具

已在 .mcp.json 配置, CC 启动时自动连接:
- **cunzhi** — 人工确认检查点 (RIPER-7 各阶段门禁)
- **augment-context-engine** — 语义代码搜索 (R/D 阶段)

### 4. 验证

```bash
/plugins                  # 查看所有插件 (应该 8 个 enabled)
/codex:setup              # 确认 Codex CLI 就绪
/mcp                      # 查看 MCP 连接 (cunzhi + augment-context)
/hooks                    # 查看 hooks (应该 6 个事件)
/doctor                   # 诊断问题
```

### 5. 安装结果检查清单
```
✅ gsd@gsd-build                              — /gsd:discuss-phase, /gsd:execute, /gsd:quick
✅ codex@openai-codex                          — /codex:rescue, /codex:review, /codex:adversarial-review
✅ superpowers@superpowers-marketplace          — brainstorm, execute-plan, plan-review
✅ everything-claude-code@everything-claude-code — npx ecc-agentshield scan
✅ playwright-skill@playwright-skill            — E2E 测试 + 截图
✅ feature-dev@claude-plugins-official           — 7阶段功能开发
✅ code-review@claude-plugins-official            — 4-agent 代码审查
✅ commit-commands@claude-plugins-official        — git workflow 增强
✅ cunzhi MCP                                   — 人工确认
✅ augment-context MCP                          — 语义搜索
✅ 6 hooks 已配置

→ 安装完成, 用 /vibe-init 初始化项目
```
