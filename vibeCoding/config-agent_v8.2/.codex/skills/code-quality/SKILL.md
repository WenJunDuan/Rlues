---
name: code-quality
description: "Linus-style six-dimension code review with manual security checks for Codex"
---

# Code Quality (Linus Taste)

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| SP requesting-code-review | Superpowers | 两阶段审查 (替代 code-review + pr-review-toolkit) | 读取 ~/.codex/superpowers/skills/requesting-code-review/SKILL.md |
| sou | MCP | 搜索代码模式 | `sou.search("变更文件")` |
| cunzhi | MCP | 严重问题寸止 | `cunzhi.confirm(TASK_DONE)` |

## 执行方式 (Codex 版)

```
1. sou.search("变更文件") → 获取变更范围
2. → SP requesting-code-review:
   Stage 1: 对照 plan.md 检查 spec compliance
   Stage 2: 代码质量审查 (见检查清单)
   降级: SP 未安装 → 直接执行两阶段
3. 手动安全检查 (替代 security-guidance plugin):
   □ 无硬编码密钥/token
   □ 公共接口输入验证
   □ SQL 参数化查询
   □ 无敏感信息泄露到日志
   □ 依赖无已知漏洞
4. Linus 四问
5. 严重问题 → 阻止，创建修复任务到 todo.md
```

## 检查清单

| 维度 | 标准 | 严重度 |
|:---|:---|:---|
| 函数长度 | <50行 | Error |
| 嵌套深度 | <3层 | Error |
| TypeScript any | 零容忍 | Error |
| 魔法数字 | 命名常量 | Warning |
| 错误处理 | 完整覆盖 | Error |
| 输入验证 | 公共接口 | Error |
| 命名 | 准确反映本质 | Warning |
| 数据结构 | 最简 | Warning |
| DRY | 无重复 | Warning |
| YAGNI | 无过度抽象 | Warning |

## Linus 四问

1. 数据结构最简？ 2. 能删掉什么？ 3. 命名准确？ 4. 有品味？

## --strict (Path C)

追加: 无未使用 import、无注释代码、无 TODO、组件<200行、单文件<500行。
