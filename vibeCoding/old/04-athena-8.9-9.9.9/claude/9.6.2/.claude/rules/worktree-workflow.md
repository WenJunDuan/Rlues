---
effort: low
attach_to_stages: [impl, ship]
attach_to_subagents: [generator]
---

<important if="starting any coding task, creating branches, or implementing features">
# Worktree Workflow · 分支隔离规范

> 适用于所有代码实现任务。违反 = REWORK（直接在 main 改代码不可接受）。

## 铁律：禁止在 main / master 直接改代码

所有实现任务 **必须** 在独立 worktree 分支上进行。

## 方式1：手动 Worktree（默认，★★★★★）

```bash
# 1. 任务开始前创建 worktree
git worktree add ../worktrees/<branch-name> -b feat/xxx

# 2. 在 worktree 路径内执行所有文件修改和提交

# 3. 任务完成，通知用户 review
# 用户 merge 后清理：
git worktree remove ../worktrees/<branch-name>
```

**适合**：个人多任务管理、不同功能独立开发、最可控。

## 方式2：Subagent + worktree（★★★★☆）

spawn Agent 时加 `isolation: "worktree"` 参数，平台自动创建和清理分支。

**适合**：单会话内并行任务，无需 agent 间通信。

## 方式3：Agent Teams（★★★☆☆，实验性）

需要多个 agent 互相协作讨论时才考虑，稳定性低。

## 分支命名（遵循 Conventional Commits）

| 前缀               | 用途          |
| ------------------ | ------------- |
| `feat/<short>`     | 新功能        |
| `fix/<short>`      | bug 修复      |
| `refactor/<short>` | 重构          |
| `chore/<short>`    | 依赖/配置更新 |

规则：

- 长度 ≤ 40 字符
- 无中文
- 无 `feature/` `bugfix/` 前缀（用 `feat/` `fix/`）

worktree 建议放在各自仓库的平级目录：`../worktrees/<branch-name>`
</important>
