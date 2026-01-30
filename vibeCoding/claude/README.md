# VibeCoding Kernel v7.9.1

> **"Talk is cheap. Show me the code."** — Linus Torvalds

AI 编程协作系统，整合 everything-claude-code 精华特性。

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

## ✨ v7.9 New Features

| Feature | Description |
|:---|:---|
| **Instinct-based Learning** | 自动学习编码模式，带置信度评分 |
| **Cunzhi MCP** | 使用 cunzhi MCP 进行寸止确认 |
| **Context7 CLI** | 使用 `npx ctx7` 替代 MCP |
| **Rules System** | 6 个核心规则文件 |
| **Iterative Retrieval** | 渐进式上下文加载 |
| **Eval Harness** | 验证循环评估框架 |
| **Cross-platform Hooks** | Node.js 跨平台 hooks |

## 📋 Quick Start

```bash
# 1. Initialize project
cd your-project
vibe-init

# 2. Start development
vibe-dev "implement user authentication"

# 3. Core commands
vibe-plan       # 任务规划 (知识库 + 经验)
vibe-review     # 代码审查 (质量 + 安全)
learn           # 提取会话模式
checkpoint      # 保存验证状态
verify          # 运行验证循环

# 4. Instinct commands (NEW)
instinct-status    # 查看学习的 instincts
instinct-export    # 导出 instincts
instinct-import    # 导入团队 instincts
evolve             # 将 instincts 演化为 skills
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  用户层        用户输入 / vibe-dev "新功能"                      │
├─────────────────────────────────────────────────────────────────┤
│  Command层     vibe-* 增强官方 / 纯自定义指令                    │
├─────────────────────────────────────────────────────────────────┤
│  Agent决策层   phase-router → 功能导向 Agents                    │
├─────────────────────────────────────────────────────────────────┤
│  Skill执行层   context7 / knowledge-base / experience / riper   │
├─────────────────────────────────────────────────────────────────┤
│  数据存储层    .ai_state/ + .knowledge/ + instincts/            │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
.claude/
├── CLAUDE.md              # 核心原则 (7条铁律)
├── orchestrator.yaml      # 配置
├── skills/                # 16 个 Skills
│   ├── context7/          # 库文档 (CLI)
│   ├── continuous-learning-v2/  # Instinct 学习
│   ├── iterative-retrieval/     # 渐进式上下文
│   ├── eval-harness/      # 评估框架
│   ├── cunzhi/            # 寸止 (MCP)
│   └── ...
├── agents/                # 7 个 Agents
│   ├── planner.md         # 计划制定
│   ├── security-reviewer.md  # 安全审查
│   └── ...
├── commands/              # 11 个命令
├── rules/                 # 6 个规则
│   ├── security.md
│   ├── coding-style.md
│   ├── testing.md
│   ├── git-workflow.md
│   ├── agents.md
│   └── performance.md
├── contexts/              # 动态上下文
├── workflows/             # PACE + 九步流程
├── hooks/                 # Hook 配置
│   └── hooks.json
└── templates/             # 项目模板

scripts/
├── lib/
│   └── utils.js           # 跨平台工具
└── hooks/
    ├── session-start.js
    ├── session-end.js
    └── pre-compact.js
```

## 🔧 Skills Overview

### Core Skills
| Skill | Purpose |
|:---|:---|
| `phase-router` | 意图识别和路由 |
| `knowledge-base` | 外部知识库读取 |
| `experience` | 经验检索和沉淀 |
| `riper` | RIPER 五步工作流 |
| `cunzhi` | 寸止协议 (MCP) |

### Enhanced Skills (v7.9)
| Skill | Purpose |
|:---|:---|
| `context7` | 库文档获取 (CLI) |
| `continuous-learning-v2` | Instinct-based 学习 |
| `iterative-retrieval` | 渐进式上下文 |
| `eval-harness` | 评估框架 |
| `verification-loop` | 检查点验证 |
| `strategic-compact` | 智能压缩建议 |

## 📜 Rules System

v7.9 引入完整的 Rules 系统：

| Rule | Purpose |
|:---|:---|
| `security.md` | 安全检查（无硬编码密钥、输入验证） |
| `coding-style.md` | 代码风格（不可变性、小函数） |
| `testing.md` | 测试规范（TDD、80%覆盖率） |
| `git-workflow.md` | Git 流程（提交格式、PR 要求） |
| `agents.md` | Agent 委托规则 |
| `performance.md` | 性能优化（模型选择、上下文管理） |

## 🔄 Instinct System

### 什么是 Instincts?

Instincts 是从编码会话中自动学习的微模式：
- 轻量级 - 单一模式，最小上下文
- 置信度评分 - 跟踪成功率
- 可演化 - 成熟后聚类为 skills

### Workflow

```bash
# 1. 自动学习（会话中自动捕获）

# 2. 查看状态
instinct-status

# 3. 导出分享
instinct-export --min-confidence=0.8

# 4. 团队导入
instinct-import team-patterns.json

# 5. 演化为 skill
evolve --tags=authentication
```

## 🔗 MCP Configuration

v7.9 需要的 MCP：

```json
{
  "mcpServers": {
    "cunzhi": {
      "command": "your-cunzhi-mcp-command",
      "description": "寸止确认 MCP"
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/sequential-thinking-mcp"],
      "optional": true
    }
  }
}
```

## 🔀 Migration from v7.8

主要变更：
1. **移除 context7 MCP** → 改用 `npx ctx7` CLI
2. **移除 mcp-feedback-enhanced** → 改用 cunzhi MCP
3. **移除 promptx** → 不再需要
4. **新增 Rules** → 6 个规则文件
5. **新增 Instincts** → continuous-learning-v2

## 📚 Credits

- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) - Instinct 系统、Rules 概念
- [Context7](https://context7.com) - 库文档系统
- Linus Torvalds - 工程哲学
- Boris Cherny - Claude Code 技术

## 📄 License

MIT
