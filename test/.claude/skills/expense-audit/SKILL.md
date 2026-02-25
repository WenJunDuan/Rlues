# expense-audit

## 适用场景
用于 `/audit` 流程中的规则判定阶段。输入来自 OCR、税务校验、历史检索、标准查询四类插件产物，输出供 `expense-auditor` 汇总到 ResultEnvelope。

## 输入契约（最小集）
- `payload.expense_report.report_id`
- `payload.expense_report.employee_id`
- `payload.expense_report.reason`
- `payload.expense_report.total_amount`
- `payload.expense_report.currency`
- `payload.expense_report.department`
- `payload.expense_report.level`
- `payload.expense_report.invoices[]`
- `payload.applicant`
- `payload.trip_application | payload.outing_application`
- `payload.policy_pack`

`invoices[]` 最小字段：
- `invoice_code`
- `invoice_number`
- `date`
- `amount`
- `category`
- `currency`

插件侧补充字段（可选）：
- `ocr.structured`
- `ocr.parser`（`filename-mvp` 表示文件名模拟解析）
- `tax_verify.status`
- `history_check.hits[]`
- `standard_query.limit`
- `standard_query.allowed_categories[]`
- `invoice_verify.used_before/status/verify_id`

## 输出契约（规则层）
规则层不直接返回 ResultEnvelope，而是返回可聚合中间结果：
- `rule_id`
- `severity` (`error | warning | info`)
- `category`
- `description`
- `evidence_ref`
- `score_delta`（对 confidence 的影响，负数）

## 执行顺序
1. `rules/invoice-authenticity.md`
2. `rules/amount-check.md`
3. `rules/duplicate.md`
4. `rules/category-match.md`

## 决策映射
1. 任一 `error` -> `decision = rejected`。
2. 无 `error` 且存在 `warning` -> `decision = needs_review`。
3. 仅 `info` 或无问题 -> `decision = approved`。
4. 若关键字段缺失（影响金额、发票唯一性或类目匹配）-> 强制降级 `needs_review`。

## 与插件边界
- `ocr`: 只负责结构化抽取，不做最终合规判定。
- `tax_verify`: 只负责税务验真与四要素一致性结果。
- `history_check`: 只返回历史命中记录，不下最终结论。
- `standard_query`: 只提供制度阈值和允许类目。
- `invoice_verify`: 只负责企业内部“是否已使用”检查，不做税务真伪判定。

## 模板与样例
- `templates/approve.md`
- `templates/reject.md`
- `templates/needs-review.md`
- `examples/pass-cases.json`
- `examples/fail-cases.json`
