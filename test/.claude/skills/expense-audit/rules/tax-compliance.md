---
rule_id: tax-compliance
version: v1
triggers: [expense-audit]
depends_on_plugins: [tax_api]
---

# 税务合规检查规则

## 规则目标
综合税务 API 验真结果与制度要求，判定发票在税务层面的合规性。

## 输入
- `invoice_data`: OCR 结构化发票数据（金额、税率、发票代码、发票号码、开票日期）
- `tax_api_result`: `tax_api` 插件返回的原始验真结果（`status`, `raw_response`）
- `policy_rules`: 适用的报销制度条文（含类目限额、税率要求等）

## 规则清单

### 1. `EXP-TAX-001` 发票验真状态检查
- `tax_api` 返回 `status: ok` 且 `raw_response` 中状态为 `verified` → 通过
- `tax_api` 返回 `status: ok` 且验真状态为 `not_found` → 标记 `error`: "发票在税务系统中未查到"
- `tax_api` 返回 `status: ok` 且验真状态为 `cancelled` → 标记 `error`: "发票已作废"
- `tax_api` 返回 `status: error` 或 `unconfigured` → 标记 `info`: "税务系统查询异常或未配置，建议人工核实"（不直接拒绝）

### 2. `EXP-TAX-002` 税率合规检查
- 对比发票上的税率与该类目应适用的税率（从 `policy_rules` 中获取）
- 税率不匹配时标记 `warning`，不直接 reject（可能是政策调整期）

### 3. `EXP-TAX-003` 金额合理性检查
- 对比发票金额与该类目的单笔限额（从 `policy_rules` 中获取）
- 超出限额 → `error`
- 接近限额（>80%）→ `warning`

## 输出示例
```json
{
  "rule_id": "EXP-TAX-001",
  "severity": "error",
  "category": "tax_compliance",
  "description": "发票在税务系统中未查到",
  "evidence_ref": "tax_api://raw_response/status",
  "score_delta": -0.4
}
```

## 决策影响
- `EXP-TAX-001` 验真失败为强拒绝信号。
- `EXP-TAX-002` 税率不匹配仅触发复核。
- `EXP-TAX-003` 超限额为拒绝，接近限额为复核。
- 税务 API 不可用时，不作为拒绝触发条件，记录 `info` 供人工判断。
