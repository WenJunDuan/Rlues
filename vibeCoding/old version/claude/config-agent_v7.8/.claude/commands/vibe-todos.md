---
name: vibe-todos
description: |
  增强版 TODO 管理。调用官方 /todos 后，叠加 Kanban 视图、进度追踪、
  优先级管理。支持任务分组和状态流转。
---

# vibe-todos Command

增强版 TODO 管理，叠加 Kanban 视图。

## 使用方式

```bash
# 查看 TODO（增强视图）
vibe-todos

# 添加 TODO
vibe-todos add "实现用户认证"

# 完成 TODO
vibe-todos done 1

# Kanban 视图
vibe-todos --kanban

# 按优先级排序
vibe-todos --sort=priority
```

## 执行流程

```
vibe-todos
    │
    ├─→ /todos                    # 1. 调用官方 /todos
    │
    ├─→ 读取 .ai_state/meta/      # 2. 加载状态
    │   ├── TODO.md
    │   └── kanban.md
    │
    ├─→ 增强显示                   # 3. Kanban 视图
    │   ├── 📋 BACKLOG
    │   ├── 🚧 IN_PROGRESS
    │   ├── 👀 REVIEW
    │   └── ✅ DONE
    │
    └─→ 更新进度统计               # 4. 进度追踪
```

## Kanban 视图

```markdown
┌─────────────┬─────────────┬─────────────┬─────────────┐
│  📋 BACKLOG │ 🚧 PROGRESS │  👀 REVIEW  │   ✅ DONE   │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ #3 添加测试 │ #1 用户认证 │ #2 API路由  │ #0 项目初始 │
│ #4 文档更新 │             │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┘

进度: ████████░░ 40% (2/5)
```

## TODO 状态

```yaml
状态流转:
  BACKLOG → IN_PROGRESS → REVIEW → DONE
            ↑___________|  (可回退)

快捷操作:
  vibe-todos start 3    # BACKLOG → IN_PROGRESS
  vibe-todos review 1   # IN_PROGRESS → REVIEW
  vibe-todos done 2     # REVIEW → DONE
  vibe-todos back 1     # 回退到上一状态
```

## 优先级

```yaml
优先级标记:
  P0: 🔴 紧急 - 立即处理
  P1: 🟠 高优 - 当天完成
  P2: 🟡 中等 - 本周完成
  P3: 🟢 低优 - 有空处理

设置优先级:
  vibe-todos priority 3 P0
```

## 与其他命令协作

```yaml
vibe-plan:
  - 生成 TODO 列表
  - 设置初始状态

/checkpoint:
  - 保存 TODO 状态
  - 支持恢复

vibe-review:
  - 检查未完成 TODO
  - 验证完成质量
```
