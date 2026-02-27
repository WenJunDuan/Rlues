# expense-audit

## 适用场景
用于 `/audit` 流程中的规则判定阶段。输入来自 OCR、tax_api 插件产物与报销单数据，输出供 `expense-auditor` 汇总到 ResultEnvelope。

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
- `ocr.parser`（`claude-vision` 表示 Claude 内置视觉识别）
- `ocr.confidence`
- `tax_api.status`（`ok | error | unconfigured`）
- `tax_api.raw_response`

## 输出契约（规则层）
规则层不直接返回 ResultEnvelope，而是返回可聚合中间结果：
- `rule_id`
- `severity` (`error | warning | info`)
- `category`
- `description`
- `evidence_ref`
- `score_delta`（对 confidence 的影响，负数）

## 执行顺序
所有规则**全部执行**后再聚合结果（不短路）：

1. `rules/amount-check.md` — 金额结构与制度限额
2. `rules/duplicate-detect.md` — 同单内重复与连号检查
3. `rules/category-match.md` — 类目与费用项对比
4. `rules/invoice-authenticity.md` — 综合验真结果与字段一致性
5. `rules/tax-compliance.md` — 综合税务 API 结果与制度要求

制度参考数据：`rules/policy-standards.md`

## 决策映射
1. 任一 `error` -> `decision = rejected`。
2. 无 `error` 且存在 `warning` -> `decision = needs_review`。
3. 仅 `info` 或无问题 -> `decision = approved`。
4. 若关键字段缺失（影响金额、发票唯一性或类目匹配）-> 强制降级 `needs_review`。

## 与插件边界（Plugin = 纯 I/O，无判定逻辑）
- `ocr`: 负责文件校验与结构化提取。默认模式下 Claude Code 通过内置 Vision 直接读取发票图片，插件仅提供文件元数据与文件名结构化提示。不做最终合规判定。
- `tax_api`: 只负责调用税务局 API，返回原始验真结果。不做业务判定。预留后期对接。

## 模板与样例
- `templates/approve.md`
- `templates/reject.md`
- `templates/needs-review.md`
- `examples/pass-cases.json`
- `examples/fail-cases.json`
