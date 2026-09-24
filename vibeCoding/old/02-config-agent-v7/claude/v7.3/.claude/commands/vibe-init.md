---
name: vibe-init
description: 初始化项目，创建.ai_state目录
---

# /vibe-init - 项目初始化

初始化VibeCoding项目状态目录。

## 触发方式

```bash
/vibe-init              # 初始化项目
/vibe-init --force      # 强制重新初始化
```

## 执行动作

### 1. 创建目录结构

```
project_document/
└── .ai_state/
    ├── active_context.md   # 当前任务状态
    ├── conventions.md      # 项目约定
    ├── decisions.md        # 决策记录
    └── hooks.log          # Stop Hooks日志
```

### 2. 初始化 active_context.md

```markdown
# Active Context State

> **异步意识**: 这是AI的唯一真理来源。

## 🎯 当前目标 (Current Goal)

> [待定义]

## 📋 任务看板

| ID | 任务 | Owner | 预估 | 状态 |
|:---|:---|:---|:---|:---|
| - | - | - | - | - |

## 🧩 关键约束

- 遵循 `.claude/skills/knowledge-bridge/` 规范
- TypeScript 无 any
- 函数 < 50行

## 📝 验证日志

[待记录]
```

### 3. 初始化 conventions.md

```markdown
# 项目约定

## 命名规范

| 类型 | 规范 | 示例 |
|:---|:---|:---|
| 组件 | PascalCase | `UserCard` |
| 函数 | camelCase | `getUserById` |
| 常量 | UPPER_SNAKE | `MAX_RETRY` |

## Git规范

| 前缀 | 用途 |
|:---|:---|
| feat | 新功能 |
| fix | 修复 |
| refactor | 重构 |
```

### 4. 初始化 decisions.md

```markdown
# 决策记录 (ADR)

## 模板

### ADR-XXX: [标题]

**日期**: YYYY-MM-DD
**状态**: 提议/已采纳/已废弃

#### 背景
[问题描述]

#### 方案
[方案对比]

#### 决策
[选择及理由]

#### 影响
[后续影响]
```

## 输出

```
✅ VibeCoding 项目初始化完成

创建文件:
- project_document/.ai_state/active_context.md
- project_document/.ai_state/conventions.md
- project_document/.ai_state/decisions.md

下一步:
- 使用 /vibe-plan 开始规划
- 或使用 /vibe-state 查看状态
```
