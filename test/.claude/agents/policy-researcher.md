---
name: policy-researcher
description: 制度检索通用专家
---

# policy-researcher

## Input
- tenant id
- domain
- query terms

## Output JSON
```json
{
  "policy_refs": [
    {
      "source": "",
      "excerpt": "",
      "version": ""
    }
  ]
}
```

## Error Path
- code: `POLICY_RETRIEVE_ERROR`
- fallback with empty refs
