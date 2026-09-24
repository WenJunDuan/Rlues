---
name: code-quality
description: "Linus-style six-dimension code review with official plugins and security scanning"
---

# Code Quality (Linus Taste)

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| 官方 code-review | Plugin | 结构化代码审查 | 手动: `/review` |
| 官方 security-guidance | Plugin | 安全漏洞检查 | 自动: 审查时扫描 |
| 官方 pr-review-toolkit | Plugin | PR 级深度审查 (Path C/D) | 手动: `/pr-review` |
| Superpowers requesting-code-review | Plugin Skill | 两阶段方法论审查 | 自动: Rev 阶段触发 |
| sou | MCP | 搜索代码模式和反模式 | `sou.search("变更文件")` |
| cunzhi | MCP | 严重问题寸止 | `cunzhi.confirm(TASK_DONE)` |

## 执行方式

```
1. sou.search("变更文件") → 获取变更范围
2. /review → 官方 code-review plugin 基础审查
3. → Superpowers requesting-code-review:
   Stage 1: 对照 plan.md 检查 spec compliance
   Stage 2: 代码质量审查 (见检查清单)
   降级: SP 未安装 → 直接执行两阶段
4. Path C/D:
   /pr-review → 官方 pr-review-toolkit: PR 级审查
   官方 security-guidance: 自动扫描安全问题
5. 结果汇总 → Linus 四问
6. 严重问题 → 阻止，创建修复任务到 todo.md
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

1. 数据结构最简？
2. 能删掉什么？
3. 命名准确？
4. 有品味？

## --strict (Path C/D)

追加: 无未使用 import、无注释代码、无 TODO、组件<200行、单文件<500行。

## 结果处理

Error → 阻止，回到 E。Warning → 建议改进。
