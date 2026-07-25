# athena-runtime-verify · playbook

> 从 SKILL.md 下沉的完整正文 (v9.9.6 渐进披露拆分)。热路径只留触发与判据。

## 循环载体: 官方 `/goal` (v9.9.6)

Codex goals 自 `rust-v0.133.0` 起 default-on 且不再 experimental —— 本 stage 的自测自改循环
由 `/goal` 承载, **不自造状态机** (铁律[不抱金饭碗讨饭])。下面的 Step 0–3 是 goal 的
完成条件与场景矩阵怎么写, 不是另一套调度器。

⚠️ goal supervisor 只读对话: 完成条件必须写成「把实跑命令 + 输出晒进对话」,
写成「跑通了」这类不可见判据会永远判不了。

## 目的

单测与静态 review 不等于真实系统可运行. 本 stage 在 impl 与 review 之间执行实际命令、真实接口或可重复 E2E, 发现问题后回 impl 修复并复跑.

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
