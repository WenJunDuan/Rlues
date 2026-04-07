---
name: vibe-review
disable-model-invocation: true
argument-hint: "[focus area]"
description: >
  单独运行质量审查。不走完整开发流程, 只审查当前代码。
---

# /vibe-review — 质量审查

## 当前状态
!`cat .ai_state/project.json 2>/dev/null | head -5`

触发 review skill, 对当前代码变更做质量审查。
焦点: $ARGUMENTS

如果 .ai_state/project.json 不存在, 按 Path A 做快速审查。
如果存在, 按当前 Path 深度做对应审查。
