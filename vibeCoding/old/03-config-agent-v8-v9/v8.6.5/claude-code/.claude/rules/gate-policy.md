# Gate Policy — 统一严重级矩阵

> Policy（该不该阻断）在此定义, Mechanism（怎么阻断）在 hooks 实现。
> 两者必须一致, 冲突时以本文件为准。

## 严重级定义

| 级别       | 行为               | 退出码             |
| :--------- | :----------------- | :----------------- |
| `block`    | 阻断交付, 必须修复 | `exit(2)`          |
| `warn`     | 输出警告, 不阻断   | stderr + `exit(0)` |
| `log-only` | 仅记录, 不影响流程 | stderr + `exit(0)` |

## 门禁规则

| 检查项                                   | 级别    | 说明                   |
| :--------------------------------------- | :------ | :--------------------- |
| doing.md 有未完成项                      | `block` | 任务未完成不能交付     |
| plan.md 有未完成项                       | `block` | 计划未完成不能交付     |
| session.md 不存在                        | `warn`  | 上下文可能丢失         |
| 测试未通过 (npm test / pytest / go test) | `block` | 不能交付失败的代码     |
| 类型检查失败 (tsc --noEmit)              | `block` | 不能交付类型错误       |
| gate 脚本自身异常                        | `warn`  | 记录错误, 提示手动审查 |

## 适用范围

- CC: `delivery-gate.cjs` (Stop hook) + `task-completed.cjs` (TaskCompleted hook)
- Codex: `delivery-gate.cjs` (Rev 阶段显式执行)
