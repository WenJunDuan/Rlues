# VibeCoding Kernel v9.3.1 — Claude Code

## 架构

```
VibeCoding (编排) ← PACE + RIPER-7 + Quality Gate
    ↓ 调用
superpowers (技能) + gstack /codex (双Agent) + 官方 plugins (工具)
ECC (安全+学习) + playwright-skill (前端调试)
```

## 安装

```bash
cp -r .claude/ settings.json plugin.json .mcp.json .gitignore /your/target/
# trust 项目后 CC 自动提示安装 7 个插件
/vibe-init
```

## 命令

```
/vibe-dev "任务"    # PACE + RIPER-7
/vibe-status        # 状态
/vibe-resume        # 断点恢复
/codex "指令"       # gstack: 调用 Codex (second opinion / 写代码)
```
