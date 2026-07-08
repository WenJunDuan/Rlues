---
schema: fullstack-delivery-report
version: 1
sprint: ""
status: draft
generated_at: ""
---

# Delivery Report Schema

交付报告使用 YAML frontmatter + Markdown 正文。frontmatter 供机器解析，正文供用户确认。

## Frontmatter 字段

```yaml
schema: fullstack-delivery-report
version: 1
sprint: "2026-xx-xx-feature"
status: "draft|ready-for-confirmation|accepted|blocked"
generated_at: "ISO-8601"
token_usage_path: "sprints/{slug}/token-usage.yaml"
requirements_total: 0
requirements_done: 0
fe_tests:
  command: ""
  total: 0
  passed: 0
  failed: 0
  evidence: []
be_tests:
  command: ""
  total: 0
  passed: 0
  failed: 0
  evidence: []
e2e_tests:
  command: ""
  total: 0
  passed: 0
  failed: 0
  evidence: []
security_tests:
  static_checks: []
  dynamic_cases: []
  high_risk_open: 0
model_usage:
  - stage: "design|impl|runtime-verify|review|ship"
    model: ""
    input_tokens: null
    output_tokens: null
    total_tokens: null
legacy_issues: []
checkpoints:
  - checkpoint_id: ""
    type: "machine-gate|human-confirmation"
    status: "pending|passed|failed|blocked|waived"
    attempt: 0
    max_failures: 3
    confirmed_by: null
    confirmed_at: null
    issue_path: null
    evidence: []
manual_confirmations:
  - checkpoint_id: ""
    confirmed_by: ""
    confirmed_at: "ISO-8601"
    decision: "accepted|rejected|accepted-with-conditions"
    notes: ""
```

## 正文结构

## 需求完成度

逐条列出 requirement id、状态、实现文件、测试证据和未完成原因。状态只允许
`done`、`partial`、`blocked`、`deferred`。

## FE 测试

列出前端 lint/typecheck/unit/component/E2E 命令、用例数、通过率、关键路径覆盖和证据路径。

## BE 测试

列出后端 compile/unit/integration/API 契约 diff 命令、用例数、通过率、关键路径覆盖和证据路径。

## 模型与 token 消耗

读取 `token_usage_path` 指向的 `token-usage.yaml`，按 `by_stage -> model` 汇总 input/output/total token。
无 hook 数据时写 `null`，正文可显示 `unknown`，不得编造。

## 遗留问题

列出问题、影响、风险等级、建议处理人、是否阻断交付。

## 人工确认清单

列出 CP1/CP3/CP5 及任何额外人工确认项，包括确认人、时间、结论、附加条件。
同时引用 `checkpoints` 中对应记录；人工确认不得只出现在正文里。
