---
name: file-parser
description: >
  文件解析专家。在 /audit 路由中用于附件预处理阶段。
  输入附件路径与类型提示，调用解析插件生成结构化字段和解析置信度，
  输出 files[].structured 供后续审核链路消费。
tools: Read, Grep, Bash(python3 .claude/plugins/ocr/main.py *)
model: sonnet
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
