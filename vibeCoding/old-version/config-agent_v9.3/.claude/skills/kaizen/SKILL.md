---
name: kaizen
description: V 阶段回顾。总结经验教训, 追踪 Agent 易犯错误到 conventions.md。每次交付后触发。
---
# Kaizen

## 流程
1. 回顾本次开发: 好的保持, 差的改进, 模式性错误?
2. 更新 .ai_state/lessons.md (技术陷阱 + 有效模式)
3. 如发现模式性错误 → conventions.md "## Agent 易犯错误" 追加
   格式: `- "具体错误 + 正确做法"`
   SessionStart 时 context-loader 会输出提醒
4. 摘要给用户
