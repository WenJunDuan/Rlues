---
name: worktrees
---

# Git Worktrees

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| git CLI | Shell | worktree 操作 | `git worktree add/remove/list` |
| commit-commands | Plugin | 提交规范 | 自动: `git commit` 时 |

## 激活条件

| Path | 方式 |
|:---|:---|
| A/B | 不激活 (普通分支或直接 commit) |
| C | E 阶段开始前自动创建 worktree |
| D | Lead worktree + teammate 子分支 |
| --worktree | 任意 Path 强制激活 |

## 流程

```
1. git status → 确认 main 干净
2. git worktree add ../project-feature feature/vibe-{id}-{desc}
3. cd worktree → RIPER-7 E 阶段开发
4. 提交 → commit-commands plugin (Conventional Commits)
5. V 阶段完成 → merge 或 PR → git worktree remove
```

## Path D 分支策略

```
Lead:  feature/vibe-{id}-main
  ├─ Teammate: feature/vibe-{id}-frontend
  ├─ Teammate: feature/vibe-{id}-backend
  └─ Teammate: feature/vibe-{id}-tests
合并顺序: tests → backend → frontend → main
```

## 降级

git worktree 不支持 → `git checkout -b` 普通分支。
