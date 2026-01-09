# VibeCoding Kernel v7.3 (VibeOS)

> **"Talk is cheap. Show me the code."** — Linus Torvalds
> **"Claude 不是聊天机器人，而是可并行调度、可验证的工程资源。"** — Boris Cherny

AI 编程协作专家系统，融合 RIPER-10 工作流、寸止协议、Linus 思维、Boris 实践和官方 Plugins。

---

## 🆕 v7.3 核心特性

| 特性                | 描述                                      |
| :------------------ | :---------------------------------------- |
| **vibe-前缀指令**   | 自定义指令使用`vibe-`前缀，避免与官方冲突 |
| **分离架构**        | Agent/Skills/Commands/MCP 完全独立        |
| **多执行技能**      | Codex、Gemini(未来)、Claude 原生可选      |
| **官方 Plugins**    | 集成 9 个官方插件                         |
| **Path C 逐步思考** | 复杂任务必须逐步推理                      |
| **.ai_state 位置**  | 统一放在`project_document/.ai_state/`     |

---

## 📁 目录结构

```
.claude/
├── CLAUDE.md              # 🔑 Bootloader
├── commands/              # vibe-前缀指令
│   ├── _index.md         # 指令索引
│   ├── vibe-plan.md      # /vibe-plan
│   ├── vibe-design.md    # /vibe-design
│   ├── vibe-code.md      # /vibe-code
│   ├── vibe-review.md    # /vibe-review
│   └── vibe-init.md      # /vibe-init
├── agents/                # 角色库
│   ├── pm.md, pdm.md, ar.md, ld.md
│   ├── qe.md, sa.md, ui.md
├── skills/                # 技能库
│   ├── codex/            # AI执行引擎
│   ├── gemini/           # 备选引擎(未来)
│   ├── thinking/         # 逐步思考
│   ├── meeting/          # 模拟会议
│   ├── verification/     # 验证回路
│   ├── knowledge-bridge/ # 知识桥接
│   ├── memory/           # 记忆管理
│   └── sou/              # 语义搜索
├── workflows/
│   ├── pace.md           # P.A.C.E.路由+逐步思考
│   └── riper.md          # RIPER-10流程
├── hooks/
│   └── stop-hooks.md     # Stop Hooks定义
├── plugins/
│   └── _index.md         # 官方Plugins索引
├── templates/
│   └── ai-state.md       # .ai_state模板
└── references/
    ├── frontend-standards.md
    ├── backend-standards.md
    └── mcp-tools.md
```

---

## 🚀 快速开始

### 1. 部署配置

```bash
cp -r .claude /your/project/
```

### 2. 初始化项目

```bash
/vibe-init
```

创建 `project_document/.ai_state/` 目录。

### 3. 使用指令

```bash
/vibe-plan      # 深度规划
/vibe-design    # 架构设计
/vibe-code      # 编码执行
/vibe-review    # 代码审查
```

---

## 🎯 自定义指令 (vibe-前缀)

| 指令           | 简写  | 描述       |
| :------------- | :---- | :--------- |
| `/vibe-plan`   | `/vp` | 深度规划   |
| `/vibe-design` | `/vd` | 架构设计   |
| `/vibe-code`   | `/vc` | 编码执行   |
| `/vibe-review` | `/vr` | 代码审查   |
| `/vibe-init`   | -     | 初始化项目 |
| `/vibe-state`  | -     | 查看状态   |

### 参数

```bash
/vibe-code --skill=codex     # 指定Codex执行
/vibe-code --path=C          # 强制Path C逐步思考
/vibe-review --strict        # 攻击性审查
```

---

## 🔌 官方 Plugins

| 插件                    | 用途     |
| :---------------------- | :------- |
| `code-review`           | 代码审查 |
| `commit-commands`       | Git 提交 |
| `feature-dev`           | 功能开发 |
| `frontend-design`       | 前端设计 |
| `pr-review-toolkit`     | PR 审查  |
| `security-guidance`     | 安全指导 |
| `learning-output-style` | 输出风格 |
| `hookify`               | 钩子系统 |
| `ralph-wiggum`          | 创意模式 |

#@# 🔌 官方 Plugins 安装

第一步：准备插件文件
如果你还没有下载源码，请先克隆仓库

```bash
mkdir -p ~/git
cd ~/git
git clone https://github.com/anthropics/claude-code.git
```

第二步：生成启动指令

```bash
claude \
  --plugin-dir ./plugins/code-review \
  --plugin-dir ./plugins/commit-commands \
  --plugin-dir ./plugins/feature-dev \
  --plugin-dir ./plugins/frontend-design \
  --plugin-dir ./plugins/learning-output-style \
  --plugin-dir ./plugins/hookify \
  --plugin-dir ./plugins/pr-review-toolkit \
  --plugin-dir ./plugins/security-guidance \
  --plugin-dir ./plugins/ralph-wiggum
```

---

## ⚡ P.A.C.E. 路由

| 路径  | 条件          | 特点                |
| :---- | :------------ | :------------------ |
| **A** | 单文件/<30 行 | 静默执行            |
| **B** | 2-10 文件     | 计划先行            |
| **C** | >10 文件      | **逐步思考+分阶段** |

---

## 🛠️ 技能选择

```bash
# Codex执行
/vibe-code --skill=codex "实现登录"

# Gemini执行（未来）
/vibe-code --skill=gemini "优化性能"

# Claude原生（默认）
/vibe-code "简单修复"
```

---

## 📍 状态位置

```
project_document/
└── .ai_state/
    ├── active_context.md   # 当前任务
    ├── conventions.md      # 项目约定
    ├── decisions.md        # 决策记录
    └── hooks.log          # 钩子日志
```

> **文件系统是唯一的真理**

---

**版本**: v7.3 | **架构**: VibeOS Modular | **协议**: RIPER-10 + 寸止
