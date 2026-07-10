# Checkpoint Protocol

checkpoint 分两类：机器门禁和人工确认。机器门禁由命令、文件、探活、测试报告等证据判定；人工确认由用户明确回复判定。

## 通用字段

- `checkpoint_id`：稳定编号，如 `CP1-ui-confirmation`。
- `type`：`machine-gate` 或 `human-confirmation`。
- `status`：`pending`、`passed`、`failed`、`blocked`、`waived`。
- `entry_stage`：进入 checkpoint 前的 PACE stage。
- `attempt`：当前尝试次数，从 0 或 1 起均可，但同一 sprint 内必须一致。
- `max_failures`：默认 3；连续达到上限后停机并记录 issue。
- `evidence_required`：必须存在且可复验的证据。
- `evidence`：本次尝试实际证据数组，含命令、退出码、文件、截图或 URL。
- `pass_condition`：通过条件。
- `fail_target`：失败后回到的最近有效子步骤，不回起点。
- `rollback_target`：机器可读回滚目标，格式建议 `{stage}:{substep}`。
- `confirmed_by`：通过者。机器门禁填工具/agent；人工确认填用户或 reviewer。
- `confirmed_at`：ISO-8601 时间；未确认时为 `null`。
- `issue_path`：失败/阻塞问题记录路径；没有则为 `null`。
- `owner`：机器、用户或指定 reviewer。

## `checkpoints.yaml` Schema

```yaml
schema: fullstack-delivery-checkpoints
version: 1
sprint: "2026-xx-xx-feature"
checkpoints:
  - checkpoint_id: "CP1-ui-confirmation"
    type: "human-confirmation"
    status: "pending"
    entry_stage: "design"
    attempt: 0
    max_failures: 3
    owner: "user"
    pass_condition: "user explicitly approves mockup"
    fail_target: "design:mockup"
    rollback_target: "design:mockup"
    confirmed_by: null
    confirmed_at: null
    issue_path: null
    evidence_required:
      - "mockup screenshot"
    evidence: []
```

状态转换：`pending -> passed|failed|blocked|waived`。`failed` 且 `attempt >= max_failures` 时必须转
`blocked`，写 `issue_path`，等待用户或 reviewer 介入。`waived` 只能由用户或明确授权 reviewer 设置，
并必须在 `evidence` 里记录原因。

## 默认回滚表

| checkpoint | 类型 | 失败回滚目标 |
|---|---|---|
| CP1 效果图确认 | human-confirmation | design: mockup/API 契约子步 |
| CP2 demo 可运行 | machine-gate | impl: scaffold-page-gen |
| CP3 schema 评审 | human-confirmation | design/impl: db-schema-gen |
| CP4 编译与基础质量 | machine-gate | impl: scaffold-module-gen |
| 集成契约 diff | machine-gate | 判定 mock 侧或 BE 侧后回对应 impl |
| E2E/安全测试 | machine-gate | runtime-verify 对应测试 skill |
| CP5 交付报告确认 | human-confirmation | runtime-verify 或 report 汇总子步 |

## 证据规则

- 检查文件、退出码、测试结果、截图、trace、探活响应和报告字段。
- 不把日志中的固定字符串当作唯一通过依据。
- 证据路径必须进入 sprint 产物或交付报告，便于 review 和 ship 复验。
- 人工确认必须记录问题、决议和时间；不得伪造用户确认。
