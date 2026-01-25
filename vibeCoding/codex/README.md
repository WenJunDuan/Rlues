# VibeCoding Kernel v7.8 for Codex CLI

> **"Talk is cheap. Show me the code."** — Linus Torvalds

AI 编程协作系统，Codex CLI 适配版本。

## 🚀 Quick Install

### Linux / macOS
```bash
git clone https://github.com/your-repo/vibecoding-kernel-codex.git
cd vibecoding-kernel-codex
./install.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/your-repo/vibecoding-kernel-codex.git
cd vibecoding-kernel-codex
.\install.ps1
```

## ✨ Features

| Feature | Description |
|:---|:---|
| **Context7 Skill** | 智能库文档获取，自动检测库引用 |
| **Continuous Learning** | 从会话自动提取可复用模式 |
| **Verification Loop** | 检查点式验证，确保代码质量 |
| **Strategic Compact** | 智能上下文压缩建议 |
| **P.A.C.E. Router** | 复杂度评估和路径选择 |
| **九步工作流** | 完整开发生命周期管理 |

## 📋 Quick Start

```bash
# 1. Initialize project
cd your-project
vibe-init

# 2. Start development
vibe-dev "implement user authentication"

# 3. Key commands
vibe-plan      # 任务规划 (知识库 + 经验)
vibe-review    # 代码审查 (质量检查)
learn          # 提取会话模式
checkpoint     # 保存验证状态
verify         # 运行验证循环
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  用户层        用户输入 / vibe-dev "新功能"                      │
├─────────────────────────────────────────────────────────────────┤
│  Command层     自定义指令                                        │
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
.codex/
├── CODEX.md               # 核心原则 (7条铁律)
├── orchestrator.yaml      # 配置
├── skills/                # 13 个 Skills
│   ├── context7/
│   ├── continuous-learning/
│   ├── verification-loop/
│   ├── strategic-compact/
│   ├── phase-router/
│   ├── knowledge-base/
│   ├── experience/
│   └── ...
├── commands/              # 7 个命令
├── agents/                # 5 个 Agent
├── contexts/              # 动态上下文
├── workflows/             # PACE + 九步流程
└── templates/             # 项目模板
```

## 🔧 Skills Overview

| Skill | Purpose |
|:---|:---|
| `context7` | 智能获取库文档 |
| `continuous-learning` | 从会话提取模式 |
| `verification-loop` | 检查点验证 |
| `strategic-compact` | 智能压缩建议 |
| `phase-router` | 意图识别和路由 |
| `knowledge-base` | 外部知识库读取 |
| `experience` | 经验检索和沉淀 |
| `riper` | RIPER 五步工作流 |
| `cunzhi` | 寸止协议（暂停确认） |

## 🔄 与 Claude Code 版本的区别

| 方面 | Claude Code | Codex CLI |
|:---|:---|:---|
| 配置目录 | `~/.claude/` | `~/.codex/` |
| 入口文件 | `CLAUDE.md` | `CODEX.md` |
| 官方命令增强 | vibe-* → /官方 | 纯自定义 |
| MCP 配置 | settings.json | config.toml |

## 📚 Documentation

- [CODEX.md](.codex/CODEX.md) - Core architecture
- [orchestrator.yaml](.codex/orchestrator.yaml) - Configuration
- [Skills Index](.codex/skills/) - All skills

## 📄 License

MIT
