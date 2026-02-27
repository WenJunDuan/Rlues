---
rule_id: invoice-authenticity
version: v2
triggers: [expense-audit]
depends_on_plugins: [ocr, tax_api]
---

# 发票真伪检查规则

## 规则目标
综合 OCR 识别结果、税务 API 验真结果和发票字段一致性，判断票据的真实性与可用性。

## 输入
- `invoice_data`: OCR 结构化发票数据
- `tax_api_result`: `tax_api` 插件返回的税务验真结果
- `ocr_confidence`: OCR 识别置信度

## 规则清单

### 1. `EXP-INV-001` OCR 置信度检查
- 整体置信度 < 70% → `warning`: "发票图像质量差，关键字段识别可能不可靠"
- 关键字段（金额、发票号）置信度 < 85% → `warning`: "关键字段识别不确定"
- 当前 OCR parser 为 `claude-vision` 时，由 Claude 内置视觉能力提供识别结果，`confidence` 可作为参考依据

### 2. `EXP-INV-002` 字段一致性检查
- 金额大小写不一致 → `error`: "发票金额大小写不匹配"
- 开票日期在未来 → `error`: "开票日期异常"
- 开票日期超过报销周期（默认 6 个月）→ `warning`: "发票超期"
- 发票代码格式不符合国家标准 → `error`: "发票代码格式异常"

### 3. `EXP-INV-003` 税务交叉验证
- OCR 结果与税务局返回信息中的关键字段（金额、发票号码、开票日期）交叉对比
- 不一致 → `error`: "发票信息与税务系统记录不匹配"
- 税务 API 未接通或异常时，记录 `info`，不直接拒绝

### 4. `EXP-INV-004` 购方信息一致性
- 购方信息与员工所属公司不匹配 → `warning`: "购方信息不一致"

## 输出示例
```json
{
  "rule_id": "EXP-INV-002",
  "severity": "error",
  "category": "invoice_authenticity",
  "description": "发票金额大小写不匹配",
  "evidence_ref": "ocr://structured/amount_check",
  "score_delta": -0.4
}
```

## 决策影响
- 发票真实性风险优先级高，命中 `error` 时直接进入拒绝路径。
- 第一关模式下（API 不可用），接口不可用不作为拒绝的直接触发条件。
