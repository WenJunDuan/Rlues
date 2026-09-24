---
name: polish
description: Refactor/System 的 polish 阶段：runtime-verify 之后、独立 review 之前，在实现 worktree 做有界清理并补架构档。
---

# polish

何时：path ∈ {Refactor, System}，runtime-verify 已完成或有 `skip_runtime_verify` 豁免。Hotfix/Bugfix/Quick/Feature 不强制。跳过要豁免 `skip_polish`（带 until 与 reason）。

## 步骤

1. `athena sprint stage polish`。
2. 派 polish-worker（或主 agent 自己做小范围清理），任务给：sprint、实现 worktree 绝对路径、允许写集、五项检查、验证命令。
3. 五项检查：
   | # | 检查 | 例 |
   |---|---|---|
   | 1 | 临时代码、调试痕迹 | `console.log`、`debugger`、无 issue 号的 TODO |
   | 2 | 注释 | 公开 API 缺 docstring、复杂逻辑缺解释 |
   | 3 | 重复 | 复制粘贴、相似函数 |
   | 4 | 低效 | N+1 查询、阻塞 IO、无谓循环 |
   | 5 | 过度设计与过度防御 | 无消费者的抽象或配置项、边界内死防御分支（rules/coding.md） |
4. 复跑受影响检查：`athena run -- <命令>`。
5. log.md 记一行 `polish: <五项结论摘要>`（A2 据此判断已做 polish）。
6. 改动 ≥5 文件：按 architect-doc 更新 `architecture/`（A3）。值得复用的决策写 `decisions/`（pace/references/decisions.md）。
7. `athena sprint stage review`，发起独立 review。

## 边界

- polish 改代码，review 不改；polish 在 review 之前。
- 不 merge、不开 PR、不删 worktree——那些在 review 通过、用户授权 ship 之后。
- worker 到轮数上限返回进度，不算完成；续做用 SendMessage。

完成条件：五项各有一行结论、检查复跑通过、log.md 有 polish 行、需要时 architecture 已更新。
