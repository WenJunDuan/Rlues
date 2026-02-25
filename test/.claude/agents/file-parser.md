---
name: file-parser
description: 文件解析通用专家
---

# file-parser

## Input
- file path list
- file type hints

## Output JSON
```json
{
  "files": [
    {
      "path": "",
      "structured": {},
      "confidence": 0.0
    }
  ]
}
```

## Error Path
- code: `FILE_PARSE_ERROR`
- return partial results when possible
