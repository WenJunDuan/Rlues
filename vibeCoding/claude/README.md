# VibeCoding Kernel v7.8

> **"Talk is cheap. Show me the code."** — Linus Torvalds

AI 编程协作系统，支持 Claude Code / Codex CLI / Gemini CLI 多引擎调度。

## 🚀 Quick Install

### Linux / macOS
```bash
git clone https://github.com/your-repo/vibecoding-kernel.git
cd vibecoding-kernel
./install.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/your-repo/vibecoding-kernel.git
cd vibecoding-kernel
.\install.ps1
```

## ✨ v7.8 New Features

| Feature | Description |
|:---|:---|
| **Context7 Skill** | 智能库文档获取，替代 MCP 按需加载 |
| **Continuous Learning** | 从会话自动提取可复用模式 |
| **Verification Loop** | 检查点式验证，确保代码质量 |
| **Strategic Compact** | 智能上下文压缩建议 |
| **Dynamic Contexts** | 开发/审查/研究模式动态注入 |

## 📋 Quick Start

```bash
# 1. Initialize project
cd your-project
vibe-init

# 2. Start development
vibe-dev "implement user authentication"

# 3. Key commands
vibe-plan      # Enhanced planning with KB + Experience
vibe-review    # Code review with quality checks
/learn         # Extract patterns from session
/checkpoint    # Save verification state
/verify        # Run verification loop
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  用户层        用户输入 / vibe-dev "新功能"                      │
├─────────────────────────────────────────────────────────────────┤
│  Command层     增强官方 + 纯自定义                               │
├─────────────────────────────────────────────────────────────────┤
│  Agent决策层   phase-router → 功能导向 Agents                    │
├─────────────────────────────────────────────────────────────────┤
│  Skill执行层   context7 / knowledge-base / experience / riper   │
├─────────────────────────────────────────────────────────────────┤
│  数据存储层    .ai_state/ + .knowledge/                         │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
.claude/
├── CLAUDE.md              # Core principles (7 rules)
├── orchestrator.yaml      # Multi-AI configuration
├── skills/                # 13 skills
│   ├── context7/          # Smart library docs
│   ├── continuous-learning/
│   ├── verification-loop/
│   ├── strategic-compact/
│   ├── phase-router/
│   ├── knowledge-base/
│   ├── experience/
│   └── ...
├── agents/                # 5 functional agents
├── commands/              # vibe-* commands
├── workflows/             # PACE + Nine-steps
├── contexts/              # dev / review / research
└── templates/             # Project templates
```

## 🔧 Skills Overview

| Skill | Purpose |
|:---|:---|
| `context7` | 智能获取库文档，无需 "use context7" |
| `continuous-learning` | 从会话提取可复用模式 |
| `verification-loop` | 检查点验证和质量门控 |
| `strategic-compact` | 智能上下文压缩建议 |
| `phase-router` | 意图识别和工作流路由 |
| `knowledge-base` | 外部知识库读取 |
| `experience` | 经验检索和沉淀 |
| `riper` | RIPER 五步工作流 |
| `cunzhi` | 寸止协议（暂停确认） |

## 📚 Documentation

- [CLAUDE.md](.claude/CLAUDE.md) - Core architecture
- [orchestrator.yaml](.claude/orchestrator.yaml) - Configuration
- [Skills Index](.claude/skills/) - All skills

## 🤝 Credits

Integrated best practices from:
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by @affaanmustafa
- [Context7](https://github.com/upstash/context7) by Upstash
- Linus Torvalds' engineering philosophy
- Boris Cherny's Claude Code techniques

## 📄 License

MIT
