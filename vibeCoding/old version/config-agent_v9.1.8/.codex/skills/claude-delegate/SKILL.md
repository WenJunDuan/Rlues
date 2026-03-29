---
name: claude-delegate
description: 调用 Claude Code 作为子代理
---
## 用途
需要 Claude 长上下文分析、细致审查、或用户要求时

## 调用: `claude -p "指令"`

## 规则
- 调用前确认用户同意
- 敏感代码不传给外部模型
- 拿到结果后在当前 agent 验证
