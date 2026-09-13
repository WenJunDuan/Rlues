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
token_usage_path: null  # available native/legacy usage artifact, otherwise null
token_usage_status: "ok|no_usage_found|partial|unavailable"
requirements_total: 0
requirements_done: 0
runtime_env_warnings: []
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
  blocked_dynamic_cases: []
  high_risk_open: 0
capability_reads:
  - capability: ""
    manifest: ""
    purpose: ""
    status: "not-run|passed|blocked|failed"
    evidence: []
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

## 运行期只读数据

列出通过 `quantum-data` 调用的 Capability Manifest、只读 capability、调用目的、权限/数据域裁决结果和脱敏证据。
未配置 MCP 或 manifest 时写 `not-run` / `blocked`，不得伪造线上数据。

## 模型与 token 消耗

读取 `token_usage_path` 指向的可用原生记录；旧 `token-usage.yaml` 与 `no_usage_found` 状态继续可读。按实际来源汇总 input/output/total token。无来源时 path/数值写 `null`、status 写 `unavailable`；有部分来源写 `partial`，不得编造。用量不可取得不阻塞功能交付，也不要求启用自建 collector。

## 遗留问题

列出问题、影响、风险等级、建议处理人、是否阻断交付。

## 人工确认清单

列出 CP1/CP3/CP5 及任何额外人工确认项，包括确认人、时间、结论、附加条件。
同时引用 `checkpoints` 中对应记录；人工确认不得只出现在正文里。

报告的需求、工件和证据引用复用 design/evidence/runtime-verify；真实全栈准入与四类业务状态断言见 [PACE fullstack contract](../../pace/references/fullstack-contract.md)。
