# 报销审核标准文件规范（通用）

> 本文件只定义“标准文件”的结构规范，不提供任何租户业务阈值。  
> 报销制度数据必须来自你提供的原始文档（PDF/Word/Markdown 等），由解析流程生成标准文件后输入审核链路。

## 目标
- 将非结构化制度文档转为可审核的结构化标准。
- 让 `skills/expense-audit` 保持通用，不与具体企业制度耦合。

## 标准文件建议路径
- `.claude/policies/<tenant_id>/<policy_id>/<policy_version>.md`

## 标准文件元数据（必填）
| 字段 | 说明 |
|---|---|
| `policy_id` | 制度唯一标识 |
| `policy_version` | 制度版本 |
| `tenant_id` | 租户标识 |
| `effective_from` | 生效日期 |
| `effective_to` | 失效日期（可为空） |
| `source_docs[]` | 原始制度文档引用（路径、标题、版本） |
| `generated_at` | 标准文件生成时间（UTC） |
| `generator` | 生成者（agent/model） |

## 标准条目（建议）
### 1. 职级限额
| level | single_limit | currency | clause_ref |
|---|---:|---|---|
| `<Lx>` | `<number>` | `<CNY>` | `<文档条款引用>` |

### 2. 部门允许类目
| department | allowed_categories[] | clause_ref |
|---|---|---|
| `<dept>` | `<cat1,cat2,...>` | `<文档条款引用>` |

### 3. 敏感类目要求
| category | required_note | required_attachment[] | severity_if_missing | clause_ref |
|---|---|---|---|---|
| `<gift>` | `<说明业务场景>` | `<审批单>` | `<warning/error>` | `<文档条款引用>` |

### 4. 税务合规约束
| item | rule | severity | clause_ref |
|---|---|---|---|
| `<invoice_status>` | `<verified required>` | `<error/info>` | `<文档条款引用>` |

### 5. 默认策略（未命中时）
| scope | fallback | severity | clause_ref |
|---|---|---|---|
| `<unknown_level>` | `<limit value or manual review>` | `<warning>` | `<文档条款引用>` |

## 与 `payload.policy_pack` 对齐
建议在 `payload.policy_pack` 中附带：

```json
{
  "policy_id": "pol-xxx",
  "policy_version": "v2026.02",
  "rules": ["amount-check", "category-match", "duplicate-detect"],
  "standard_file": ".claude/policies/t-1/pol-xxx/v2026.02.md",
  "source_docs": [
    {
      "path": "docs/finance/reimbursement-policy-2026.pdf",
      "title": "报销制度 2026 版",
      "version": "2026.02"
    }
  ]
}
```

## 生成要求
1. 所有阈值都要可追溯到 `source_docs` 条款。
2. 条款含糊或冲突时不猜测，标记为 `needs_review` 并保留冲突证据。
3. 标准文件更新后必须同步提升 `policy_version`。
