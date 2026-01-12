# VibeCoding Kernel v7.5

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

## 🆕 v7.5 新特性

| 特性 | 说明 |
|:---|:---|
| **code-simplifier** | 开发时自动简化代码，Linus品味守护 |
| **双轨记忆** | 项目状态 → 文件，通用知识 → Memory MCP |
| **强制TODO流程** | 所有路径都必须生成TODO并核对 |
| **错误学习** | 自动从Bug中学习，记录教训 |
| **Git工作流** | 规范分支策略和提交规范 |
| **调试技能** | 系统化调试方法 |
| **性能优化** | 性能问题检测和优化 |
| **细化RIPER** | 每个阶段更详细的步骤 |

---

## 🧠 记忆分离原则

v7.5 最重要的改进：**项目状态和通用知识分离**

```
项目状态 (.ai_state/)          通用知识 (Memory MCP)
──────────────────────────     ──────────────────────────
✅ 当前任务 TODO               ✅ 用户偏好
✅ 项目进度                    ✅ 禁止动作（用户指出的）
✅ 项目技术决策                ✅ 高频动作和方法
✅ AI交接记录                  ✅ 代码模式
                              ✅ 错误教训
```

用户说"以后不要做XXX"，会自动记录到 Memory MCP。

---

## 📁 目录结构

```
config-agent_v7.5/
├── README.md                    # 本文件
├── plugins-guide.md             # 官方 Plugin 配置指南
│
└── .claude/
    ├── CLAUDE.md                # AI 入口文件
    ├── orchestrator.yaml        # AI 调度配置
    │
    ├── agents/                  # 角色定义 (8个)
    │   └── pm, pdm, ar, ld, qe, sa, ui, orchestrator
    │
    ├── skills/                  # 技能定义 (15个)
    │   ├── codex/              # Codex 执行引擎
    │   ├── gemini/             # Gemini 执行引擎
    │   ├── thinking/           # 深度推理
    │   ├── verification/       # 验证回路
    │   ├── meeting/            # 多角色会议
    │   ├── memory/             # 增强记忆（双轨分离）
    │   ├── sou/                # 代码搜索
    │   ├── knowledge-bridge/   # 知识桥接
    │   ├── multi-ai-sync/      # 多 AI 同步
    │   ├── user-guide/         # 用户操作指南
    │   ├── code-simplifier/    # 🆕 代码简化器
    │   ├── error-learning/     # 🆕 错误学习
    │   ├── git-workflow/       # 🆕 Git 工作流
    │   ├── debug/              # 🆕 调试技能
    │   └── performance/        # 🆕 性能优化
    │
    ├── commands/                # 自定义指令 (6个)
    │   └── vibe-plan, vibe-design, vibe-code, vibe-review, vibe-init
    │
    ├── workflows/               # 工作流 (细化版)
    │   ├── pace.md             # P.A.C.E. 复杂度路由
    │   └── riper.md            # RIPER-10 执行循环
    │
    ├── hooks/                   # 钩子
    ├── references/              # 参考文档
    └── templates/               # 模板
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
| `/vibe-state` | - | 查看状态 |

### 参数

```bash
/vibe-code --engine=codex "实现登录功能"   # 指定引擎
/vibe-code --tdd "实现用户注册"            # TDD模式
/vibe-code --path=C "重构认证系统"         # 强制Path C
/vibe-review --strict                      # 攻击性审查
```

---

## 📋 强制 TODO 流程

**v7.5 核心改进**：无论简单还是复杂，都必须：

```
1. 生成 TODO 列表
2. 执行开发
3. 根据 TODO 逐项核对
4. 调用寸止与用户确认
```

这确保了所有任务都有明确的验收标准和完成检查。

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

## 🛑 寸止协议

关键决策点必须停止等待用户确认：

| Token | 触发条件 |
|:---|:---|
| `[PLAN_READY]` | TODO生成完成 |
| `[DESIGN_FREEZE]` | 接口定义完成 |
| `[PRE_COMMIT]` | 大规模修改前 |
| `[PHASE_DONE]` | Phase完成 |
| `[TASK_DONE]` | TODO全部完成 |

---

## 📖 核心文档

| 文档 | 说明 |
|:---|:---|
| [用户操作指南](.claude/skills/user-guide/SKILL.md) | 给用户看的操作手册 |
| [多AI同步协议](.claude/skills/multi-ai-sync/SKILL.md) | 多AI协调机制 |
| [代码简化器](.claude/skills/code-simplifier/SKILL.md) | Linus品味守护 |
| [记忆系统](.claude/skills/memory/SKILL.md) | 双轨记忆分离 |
| [错误学习](.claude/skills/error-learning/SKILL.md) | 从Bug中学习 |
| [PACE工作流](.claude/workflows/pace.md) | 复杂度路由详解 |
| [RIPER循环](.claude/workflows/riper.md) | 执行循环详解 |
| [Plugin指南](plugins-guide.md) | 官方Plugin配置 |

---

## 📊 v7.4 → v7.5 变更

| 类别 | 变更 |
|:---|:---|
| **新增技能** | code-simplifier, error-learning, git-workflow, debug, performance |
| **增强技能** | memory (双轨分离) |
| **工作流** | pace.md 和 riper.md 全面细化 |
| **核心流程** | 强制 TODO 生成和核对 |
| **记忆策略** | 项目状态与通用知识分离 |
| **文件总数** | 35 → 40 |

---

## ⚡ 核心原则

1. **用户指令优先** — 用户说的比配置重要
2. **必须生成TODO** — 无论简单还是复杂
3. **必须核对TODO** — 执行完必须检查
4. **用户纠正必记录** — 禁止动作写入Memory
5. **文件系统是唯一真理** — 不依赖会话记忆
6. **从错误中学习** — 教训记录到Memory

---

**版本**: v7.5 | **架构**: VibeOS Modular | **哲学**: Linus + Boris
