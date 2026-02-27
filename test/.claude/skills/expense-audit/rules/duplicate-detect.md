---
rule_id: duplicate-detect
version: v1
triggers: [expense-audit]
---

# 发票查重检查规则

## 规则目标
基于报销单提交的发票数据，分析并判定是否存在重复报销风险。

## 输入
- `invoice_data`: 当前发票的结构化数据
- `expense_report.invoices[]`: 当前报销单内全部发票
- `expense_report.employee_id`: 当前报销人
- `task_id`: 当前任务 ID

## 规则清单

### 1. `EXP-DUP-001` 同单内重复
- 同一报销单内 `invoice_code + invoice_number + date` 不可重复。
- 命中 → `error`: "同一报销单内存在重复发票"

### 2. `EXP-DUP-002` 连号检查
- 同一批次提交的发票存在连号 → `warning`: "发票连号，建议核实"

### 3. `EXP-DUP-003` 同人同期异常
- 同一员工 + 同一类目 + 同期内多张发票 → `warning`: "同期同类目多张发票，建议核实"

## 输出示例
```json
{
  "rule_id": "EXP-DUP-001",
  "severity": "error",
  "category": "duplicate",
  "description": "同一报销单内存在重复发票",
  "evidence_ref": "rule://duplicate-detect/intra-report",
  "score_delta": -0.45
}
```

## 决策影响
- `EXP-DUP-001` 命中为强拒绝信号。
- `EXP-DUP-002/003` 仅触发复核，不直接拒绝。
