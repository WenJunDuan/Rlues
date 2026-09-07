---
name: polish
description: PACE Refactor/System polish；runtime-verify 完成后、最终 review 前清理代码并更新架构。
---

# /polish — Polish stage (v9.9.9)

## 触发

path ∈ {Refactor, System} 且 runtime-verify 已完成（或 skip_runtime_verify 已有效设置）→ 主 agent 进 polish。会改代码的清理 **在一次独立 review 之前**。

`_index.skip_polish = true` 时直接进入 review（用户自负责，不推荐）。

## 5 检查项

| # | 检查 | 例 |
|---|---|---|
| 1 | 临时代码 / 调试痕迹 | `console.log` / `print` / `debugger` / 无 issue 号的 TODO |
| 2 | 注释完整性 | 公开 API 缺 docstring / 复杂逻辑缺解释 |
| 3 | 冗余 / 重复代码 | 复制粘贴 / 相似函数 |
| 4 | 低效模式 | N+1 query / 阻塞 IO / 无谓循环 |
| 5 | 过度设计与过度防御 (铁律[反过度工程]) | 无消费者的抽象/配置项; 边界内死防御分支 |

## 例外

- 路径 ∈ {Hotfix, Bugfix, Quick, Feature}: 不强制 polish
- 主 agent 分派已绑定 writer，在既有实现 worktree 串行清理；**polish-worker 每次任务最多 70 轮；到限返回进度，不把截断当完成**

## 详细 playbook

完整检查项细则、模板与联动见 `references/playbook.md`。
