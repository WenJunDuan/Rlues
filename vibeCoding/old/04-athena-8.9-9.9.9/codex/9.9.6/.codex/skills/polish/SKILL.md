---
name: polish
description: PACE polish stage，Refactor/System 强制。review PASS 后做清理并触发 architecture 更新时触发。
---

# /polish — Polish stage (v9.9.6, Codex)

## 触发

最新数字 passN VERDICT = PASS 且 path ∈ {Refactor, System} → 主 agent 进 polish；CONCERNS 不得进入 polish/ship.

或主 agent 根据 evaluator VERDICT 设置 `next_action = "polish"`.

## 5 检查项 (沿用 v9.6.2)

| # | 检查 | 例 |
|---|---|---|
| 1 | 临时代码 / 调试痕迹 | `console.log` / `print` / `debugger` / `TODO/FIXME` |
| 2 | 注释完整性 | 公开 API 缺 docstring / 复杂逻辑缺解释 |
| 3 | 冗余 / 重复代码 | 复制粘贴 / 相似函数 |
| 4 | 低效模式 | N+1 query / 阻塞 IO / 无谓循环 |
| 5 | 过度设计与过度防御 (铁律[反过度工程]) | 无消费者的抽象/配置项; 边界内死防御分支 (blanket try-catch / 静默 fallback / 逐层校验); 判据: 删掉后测试仍全绿 = 删 |

## 例外

- `_index.skip_polish = true`: 跳过 polish, 直接 ship (用户自负责)
- 路径 ∈ {Hotfix, Bugfix, Quick, Feature}: 不强制 polish (本身不进 polish stage)

## 详细 playbook

完整检查项细则、模板与联动见 `references/playbook.md` —— 按需 Read, 不进热路径。
