---
name: athena-runtime-verify
description: PACE impl 后的运行时验证环 (Codex). 实跑接口、CLI 或 UI, 覆盖正常/边界/失败场景并自测自改. System/Refactor 强制, Feature 可选; 仅在用户显式要求或已有 Goal 时用 Goals 承载.
---

# /athena-runtime-verify — 运行时验证环 (v9.9.2, Codex)

## 目的

单测与静态 review 不等于真实系统可运行. 本 stage 在 impl 与 review 之间执行实际命令、真实接口或可重复 E2E, 发现问题后回 impl 修复并复跑.

## 触发

| 路径 | 要求 |
|---|---|
| Hotfix / Bugfix / Quick | 默认跳过; fix-note 可含定点实跑 |
| Feature | 外部接口、有状态或多环境时启用 |
| Refactor / System | 强制 |

## Step 0 · Readiness

开环前写清:

1. 可判失败的 checker: test/typecheck/lint/HTTP 断言/delivery-gate.
2. 最大迭代数或时间上限.
3. 允许修改的文件范围与禁止触碰的环境.
4. 状态落盘路径: `sprints/{current_sprint_slug}/runtime-verify.md`.

任一缺失, 先补再实跑.

## Step 1 · 场景矩阵

至少覆盖:

- 正常: 主业务路径真实可用
- 边界: 空值、极值、重复、并发或权限边界中适用项
- 失败: 外部依赖失败、非法输入、超时或降级中适用项
- 环境: 本机必跑; `_index.tools_available.vm_available=true` 时按 `/athena-vm doctor` 结果决定是否增加 VM

前端/E2E 优先 `$playwright`; 后端/API 用真实 HTTP 或测试库; CLI 用实际命令、退出码与 stdout/stderr 断言.

## Step 2 · 执行循环

1. 运行一个可重复场景并保留命令与关键输出.
2. 失败则定位原因; 需要改代码时回 impl, 按写入路由分派 generator.
3. 修复后复跑失败场景与相关回归场景.
4. 达到完成条件或预算上限后停止; 不无限循环, 不把 unknown 当 pass.

普通 workflow 足以完成本环. 只有用户显式要求 Goal, 或当前线程已有 Goal 时, 才把上述完成条件交给 Goals 承载; 本 skill 不自行创建 Goal.

密集测试如需隔离, 用 `spawn_agent` 分派有界任务; 任务消息必须包含 worktree 绝对路径、写集和验证命令.

## Step 3 · Reflect

对照 design 与实跑证据回答:

- 哪些验收已覆盖?
- 哪些场景未运行, 原因是什么?
- 是否出现新缺口需要回 impl?
- 剩余风险是否允许进入 review?

reflect 只检查本 sprint 完整性, 不发散新需求.

## 产出

主 agent 写 `sprints/{current_sprint_slug}/runtime-verify.md`, 至少包含:

- `## 完成条件与停止条件`
- `## 测试场景`
- `## 自测自改记录`
- `## Reflect`
- `## VERDICT`

每个场景记录命令、环境、关键实际输出与 PASS/FAIL/BLOCKED. 未运行的场景不得标 PASS.

## delivery-gate

System/Refactor 在 ship 时必须存在 runtime-verify.md 且含测试场景与 VERDICT. `skip_runtime_verify=true` 仅用于确无可运行表面的库/算法, 并在 design 中写清理由.

## 不做

- 不替代 impl 单测或 review
- 不对生产或共享环境做破坏性验证, 除非用户明确授权目标与范围
- 不从本地文件猜账号、密码、cookie 或 token
- 不用人工描述代替可复跑证据
