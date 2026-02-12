---
name: brainstorm
description: "R/D phase enhancement: Socratic questioning, ADR writing, and design confirmation via cunzhi"
---

# Brainstorm (R/D 阶段增强)

不重复 Superpowers brainstorming 方法论。只做 VibeCoding 特有的增强。

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| SP brainstorming | Superpowers | 苏格拉底提问+方案探索 | 读取 ~/.codex/superpowers/skills/brainstorming/SKILL.md |
| sou | MCP | 搜索现有代码和架构 | `sou.search("关键词")` |
| deepwiki | MCP | 技术领域调研 | `deepwiki.query("主题")` |
| cunzhi | MCP | D 阶段确认方案 | `cunzhi.confirm(DESIGN_READY)` |

## R 阶段增强

```
SP brainstorming 之前:
  1. sou.search("任务关键词") → 了解现有代码结构
  2. 读 .ai_state/conventions.md → 项目约定
  3. 读 .knowledge/experience/ → 相关经验

SP brainstorming 之后:
  4. 输出需求理解摘要 (不写文件，不写代码)
```

## D 阶段增强

```
SP brainstorming 之前:
  1. deepwiki.query("方案技术关键词") → 技术选型参考

SP brainstorming 之后:
  2. 写 .ai_state/decisions.md (ADR 格式):
     ### ADR-{{id}}: {{标题}}
     - 背景 / 方案 A / 方案 B / 决定 / 原因
  3. cunzhi [DESIGN_READY] → 寸止确认方案
```

## 降级

SP 未安装 → 直接执行苏格拉底提问:
- R: 围绕 范围/约束/验收 提问 5-8 个问题
- D: 自行列出 2-3 方案 + trade-off + 推荐
- ADR 写入和 cunzhi 确认不变
