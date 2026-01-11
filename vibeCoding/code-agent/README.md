# VibeCoding Kernel v7.4

> **"Talk is cheap. Show me the code."** — Linus Torvalds
> **"Claude不是聊天机器人，而是可并行调度、可验证的工程资源。"** — Boris Cherny

AI 编程协作系统，支持 Claude Code / Codex CLI / Gemini CLI 多引擎调度。

---

## 🚀 快速开始

### 1. 复制到项目

```bash
cp -r .claude your-project/
cp orchestrator.yaml your-project/.claude/
```

### 2. 初始化项目

```bash
/vibe-init
```

### 3. 开始使用

```bash
/vibe-plan "我想做一个博客系统"
```

---

## 📁 目录结构

```
config-agent_v7.4/
├── README.md                    # 本文件
├── plugins-guide.md             # 官方 Plugin 配置指南
│
└── .claude/
    ├── CLAUDE.md                # AI 入口文件
    ├── orchestrator.yaml        # AI 调度配置
    │
    ├── agents/                  # 角色定义
    │   ├── pm.md               # 项目经理
    │   ├── pdm.md              # 产品经理
    │   ├── ar.md               # 架构师
    │   ├── ld.md               # 开发工程师
    │   ├── qe.md               # 质量工程师
    │   ├── sa.md               # 安全审计
    │   ├── ui.md               # UI设计师
    │   └── orchestrator.md     # 调度中心
    │
    ├── skills/                  # 技能定义
    │   ├── codex/              # Codex 执行引擎
    │   ├── gemini/             # Gemini 执行引擎
    │   ├── thinking/           # 深度推理
    │   ├── verification/       # 验证回路
    │   ├── meeting/            # 多角色会议
    │   ├── memory/             # 记忆管理
    │   ├── sou/                # 代码搜索
    │   ├── knowledge-bridge/   # 知识桥接
    │   ├── multi-ai-sync/      # 🆕 多 AI 同步
    │   └── user-guide/         # 🆕 用户操作指南
    │
    ├── commands/                # 自定义指令
    │   ├── vibe-plan.md        # 规划模式
    │   ├── vibe-design.md      # 设计模式
    │   ├── vibe-code.md        # 编码模式
    │   ├── vibe-review.md      # 审查模式
    │   └── vibe-init.md        # 初始化
    │
    ├── workflows/               # 工作流
    │   ├── pace.md             # P.A.C.E. 复杂度路由
    │   └── riper.md            # RIPER-10 执行循环
    │
    ├── hooks/                   # 钩子
    │   └── stop-hooks.md       # 寸止协议
    │
    ├── references/              # 参考文档
    │   ├── frontend-standards.md
    │   ├── backend-standards.md
    │   └── mcp-tools.md
    │
    └── templates/               # 模板
        ├── ai-state.md
        └── kanban.md
```

---

## 🎯 核心指令

| 指令 | 简写 | 描述 |
|:---|:---|:---|
| `/vibe-plan` | `/vp` | 深度规划模式 |
| `/vibe-design` | `/vd` | 架构设计模式 |
| `/vibe-code` | `/vc` | 编码执行模式 |
| `/vibe-review` | `/vr` | 代码审查模式 |
| `/vibe-init` | - | 初始化项目 |

### 指定执行引擎

```bash
/vibe-code --engine=codex "实现登录功能"
/vibe-code --engine=gemini "优化性能"
```

---

## 🔧 AI 调度配置

编辑 `orchestrator.yaml`：

```yaml
# 默认引擎
default_engine:
  name: claude-code

# 角色映射（可选）
role_engine_mapping:
  ld: codex    # 开发者使用 codex

# 并行配置
parallel:
  enabled: true
  max_concurrent: 3
```

**优先级**: 用户指令 > 角色映射 > 默认引擎

---

## 🔄 多 AI 协调

详见 `.claude/skills/multi-ai-sync/SKILL.md`

核心原则：
1. **文件系统是唯一真理** — `project_document/.ai_state/`
2. **任务单一所有权** — 防止冲突
3. **显式交接** — 通过 `handoff.md`
4. **锁机制** — `.ai_lock` 防并发

---

## 📦 官方 Plugins

从 GitHub 复制到 `.claude/commands/`：

```bash
git clone https://github.com/anthropics/claude-code.git temp
cp temp/.claude/commands/code-review.md .claude/commands/
rm -rf temp
```

详见 `plugins-guide.md`

---

## 🛑 寸止协议

关键决策点必须停止等待用户确认：

| Token | 触发条件 |
|:---|:---|
| `[PLAN_READY]` | 任务拆解完成 |
| `[DESIGN_FREEZE]` | 接口定义完成 |
| `[PRE_COMMIT]` | 大规模修改前 |
| `[TASK_DONE]` | 任务完成 |

---

## 📋 v7.4 更新内容

- 🆕 `orchestrator.yaml` — AI 调度配置化
- 🆕 `multi-ai-sync/` — 多 AI 协调同步协议
- 🆕 `user-guide/` — 用户操作指南
- 🆕 `--engine` 参数 — 用户指定执行引擎
- 🆕 `kanban.md` — 可视化进度看板

---

## 📖 更多文档

- [用户操作指南](.claude/skills/user-guide/SKILL.md)
- [多 AI 同步协议](.claude/skills/multi-ai-sync/SKILL.md)
- [Plugin 配置指南](plugins-guide.md)

---

**版本**: v7.4 | **架构**: VibeOS Modular | **哲学**: Linus + Boris
