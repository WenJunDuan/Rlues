---
name: ai-state-template
description: 项目状态文件模板
location: project_document/.ai_state/
---

# .ai_state 项目状态模板

## 目录位置

```
project_document/
└── .ai_state/
    ├── active_context.md   # 当前任务状态（必须）
    ├── conventions.md      # 项目约定（可选）
    ├── decisions.md        # 决策记录（可选）
    └── hooks.log          # Stop Hooks日志（自动）
```

---

## active_context.md 模板

```markdown
# Active Context State

> **异步意识**: 这是AI的唯一真理来源。

## 🎯 当前目标

> [里程碑描述]

## 📋 Phase 1: [阶段名]

| ID | 任务 | Owner | 预估 | 状态 |
|:---|:---|:---|:---|:---|
| T-001 | | LD | 1h | ⏳ |

## 🏗️ 技术方案

### 数据结构
```typescript
interface User {
  id: string;
}
```

## ⚠️ 风险清单

| 风险 | 缓解措施 |
|:---|:---|

## 📝 验证日志

### [日期] T-001
- **状态**: ✅/❌
- **验证**: [证据]
```

---

## conventions.md 模板

```markdown
# 项目约定

## 命名规范
| 类型 | 规范 |
|:---|:---|
| 组件 | PascalCase |
| 函数 | camelCase |

## Git规范
| 前缀 | 用途 |
|:---|:---|
| feat | 新功能 |
| fix | 修复 |
```

---

## decisions.md 模板

```markdown
# 决策记录 (ADR)

## ADR-001: [标题]

**日期**: YYYY-MM-DD
**状态**: 已采纳

### 背景
[问题描述]

### 方案
[方案对比]

### 决策
[选择及理由]
```

---

## 初始化命令

```bash
/vibe-init
```

自动创建 `project_document/.ai_state/` 目录和模板文件。
