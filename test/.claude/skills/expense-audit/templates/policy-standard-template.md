# 报销审核标准文件模板

> 使用方式：你提供制度文档后，由 `policy-researcher` 按本模板提炼并落盘。  
> 约束：所有数值必须可追溯到原始条款；不允许凭经验补齐。

## Metadata
- policy_id: `<policy-id>`
- policy_version: `<version>`
- tenant_id: `<tenant-id>`
- effective_from: `<YYYY-MM-DD>`
- effective_to: `<YYYY-MM-DD | null>`
- generated_at_utc: `<ISO-8601>`
- generator: `<agent/model>`

## Source Docs
| path | title | version | note |
|---|---|---|---|
| `<path>` | `<title>` | `<version>` | `<optional>` |

## Level Limits
| level | single_limit | currency | clause_ref |
|---|---:|---|---|
| `<Lx>` | `<0>` | `<CNY>` | `<doc#clause>` |

## Department Categories
| department | allowed_categories | forbidden_categories | clause_ref |
|---|---|---|---|
| `<dept>` | `<cat1,cat2>` | `<cat3>` | `<doc#clause>` |

## Sensitive Categories
| category | required_note | required_attachments | severity_if_missing | clause_ref |
|---|---|---|---|---|
| `<gift>` | `<business context>` | `<approval-form>` | `<warning/error>` | `<doc#clause>` |

## Tax Compliance
| item | requirement | severity_if_violate | clause_ref |
|---|---|---|---|
| `<invoice_status>` | `<verified>` | `<error>` | `<doc#clause>` |

## Fallback Policies
| scope | fallback_action | severity | clause_ref |
|---|---|---|---|
| `<unknown_level>` | `<needs_review>` | `<warning>` | `<doc#clause>` |

## Mapping To policy_pack
```json
{
  "policy_id": "<policy-id>",
  "policy_version": "<version>",
  "rules": [
    "amount-check",
    "duplicate-detect",
    "category-match",
    "invoice-authenticity",
    "tax-compliance"
  ],
  "standard_file": "<this-file-path>",
  "source_docs": [
    {
      "path": "<doc-path>",
      "title": "<doc-title>",
      "version": "<doc-version>"
    }
  ]
}
```
