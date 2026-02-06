---
name: code-quality
description: |
  Linus-style code quality enforcement. Checks taste, simplicity,
  and engineering rigor.
---

# Code Quality Skill (Linus Taste Check)

## 检查清单

| 维度 | 标准 | 严重度 |
|:---|:---|:---|
| 函数长度 | <50行 | Error |
| 嵌套深度 | <3层 | Error |
| TypeScript any | 零容忍 | Error |
| 魔法数字 | 必须命名常量 | Warning |
| 错误处理 | 完整覆盖 | Error |
| 输入验证 | 公共接口必须 | Error |
| 命名 | 准确反映本质 | Warning |
| 数据结构 | 最简设计 | Warning |
| 重复代码 | DRY | Warning |
| 过度抽象 | YAGNI | Warning |

## Linus 四问

每次 review 时回答：
1. 数据结构是最简的吗？
2. 能删掉什么？
3. 命名准确吗？
4. 这段代码有"品味"吗？

## --strict 模式额外检查

- 无未使用的 import
- 无注释掉的代码
- 无 TODO 在提交代码中
- 组件 <200 行
- 单文件 <500 行
