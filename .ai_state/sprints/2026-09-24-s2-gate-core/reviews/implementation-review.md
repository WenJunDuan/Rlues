# Implementation review — S2 gate-core

独立 reviewer：general-purpose 子 agent（同一会话派生，非作者上下文；bundle 只读副本 + 对抗探针）。

| 轮 | 结论 | 要点 | 处置 |
|---|---|---|---|
| r1 | REWORK | P1×3：`athena run --kind`/argv 未引号 → 凭空证据；CX `workdir` 改变受管项目；`_index` 无法解析读作 idle。P2×10（未知 stage 放行推送、assume-unchanged 隐藏修改、`review_ignore: ["**"]`、`\|\|`/exit 前置、运行中树变化、CX path 覆盖 patch 头与 shell 调 apply_patch、CX isolation 字段、强推形态、超时、`-ec` 组合旗标） | 全部修复 + test_gate_regressions.py |
| r2 | REWORK | P1：`(`/`)` 分词后子 shell 内 `cd` 移动推送目标（回归）。P2：skip-worktree 未清（--stdin 无效）、invalid 状态 Stop 过拦、`bash -lc "apply_patch <<"`、账本守卫口径、trap/alias/函数遮蔽、保留字未剥 | 全部修复；声明缺口入 design |
| r3 | REWORK | P1：剥保留字后 `then cd`/`do cd`/`! cd` 被当顶层 cd（回归）。P2：`\|\|`/`&&` 后的 cd、账本守卫符号链接与大小写、`function x`/`source`、mv 目录目标等 | 只接受行首连续 cd；realExisting + 大小写不敏感；补规则与 fixture |
| r4 | REWORK | P1：`nohup/timeout/nice cd` 被当内建 cd（r2 包装剥离引入）。P2：venv `source activate` 与路径前缀工具无法产出可证证据 | 只认原始首词 `cd`；activate 豁免 + 路径前缀/uv·poetry run 分类 |
| r5 | CONCERNS | P2：绝对路径/仓库外工具被分类为 test（r5 引入）。P3：仓库外 activate、无 x 权限目录 cd | 前缀限相对且无 `..`；activate 限仓库内相对路径；resolveDir 加 X_OK；reviewer 明示「不需要再审一轮」 |

最终：无 P0/P1；P2/P3 均修复或在 design「已裁量偏差」中声明（计算出的命令词、非网络 `\| bash`、git alias push、解释器一行写账本、tar/unzip、gitignored 工具替换、未知状态 Stop 仅警告→S4 `athena ship` 严格重跑）。

VERDICT: PASS（r5 CONCERNS 项已按建议修复并加回归 fixture，89/89 绿）
