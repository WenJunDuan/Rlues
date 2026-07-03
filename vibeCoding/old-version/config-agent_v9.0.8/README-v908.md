# VibeCoding Kernel v9.0.8

AI 编程协作框架 — 将工程化思维融入 AI 编程工作流

## 变更 (v9.0.5 → v9.0.8)

**修复 16 个 Bug** (7 CRITICAL + 6 HIGH + 3 MEDIUM)

### Claude Code
- 新增 `.mcp.json` (MCP servers 移至官方推荐位置)
- 新增 `.claude-plugin/plugin.json` (可通过 /plugin install 安装)
- settings.json 添加 `$schema` (IDE 自动补全)
- 移除 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` (agents 已内置)
- settings.json 添加 deny rules (安全加固)
- SubagentStop prompt hook 修复 JSON 格式要求

### Codex CLI
- **修复** `sandbox_mode`: `workspace_write` → `workspace-write` (连字符)
- **修复** `[features]`: 移除虚构 flag (collab/plan_tool/rmcp_client), 添加官方 flag (multi_agent/collaboration_modes/apply_patch_freeform/shell_tool)
- **修复** web_search: `[web_search] table` → root-level `web_search = "live"`
- **移除** `[command_attribution]` (不存在的配置)
- **移除** hooks 目录 (Codex CLI 无 hooks 系统)
- **新增** `approval_policy = "on-request"`
- **新增** `[agents]` 配置 (max_threads/max_depth + 角色定义)
- **新增** `[sandbox_workspace_write]` 配置 (network_access=true)
- **新增** agent 角色 TOML (builder.toml/reviewer.toml/explorer.toml)
- AGENTS.md 修复术语: collab → multi_agent + collaboration_modes

### 验证来源
- Claude Code: https://code.claude.com/docs/en/settings
- Claude Code Hooks: https://code.claude.com/docs/en/hooks
- Claude Code Plugins: https://code.claude.com/docs/en/plugins
- Codex CLI Config: https://developers.openai.com/codex/config-reference/
- Codex CLI Sample: https://developers.openai.com/codex/config-sample/
- Codex CLI Multi-Agent: https://developers.openai.com/codex/multi-agent/

## 安装

### Claude Code
```bash
# 方式 1: 插件安装
/plugin install vibecoding-kernel

# 方式 2: 手动复制
cp -r cc/.claude/ your-project/.claude/
cp cc/.mcp.json your-project/.mcp.json
cp cc/.claude-plugin/ your-project/.claude-plugin/
```

### Codex CLI
```bash
cp codex/.codex/ your-project/.codex/
cp codex/AGENTS.md your-project/AGENTS.md
```

## 使用
```
/vibe-dev {需求}     # 自动路由, 开始开发
/vibe-init           # 初始化项目状态
/vibe-resume         # 中断恢复
/vibe-status         # 查看进度
```
