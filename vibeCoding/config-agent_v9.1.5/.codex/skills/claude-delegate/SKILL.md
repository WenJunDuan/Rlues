---
name: claude-delegate
description: 将任务委派给 Claude Code (Opus 4.6 / Sonnet 4.6) 执行
---
## 何时使用
- 需要 Claude 的长上下文分析能力 (1M context)
- 需要 "第二意见" 交叉验证
- 用户明确要求

## 何时不使用
- 当前任务 Codex 完全能胜任 (默认不委派)
- 未确认用户安装了 Claude Code

## 调用方式
```bash
# 单次任务
claude -p "$ARGUMENTS" --output-format text

# 指定模型
claude -p "$ARGUMENTS" --model sonnet --output-format text

# 代码审查
claude -p "Review these changes: $(git diff)" --output-format text
```

## 注意
- 需用户已安装: `npm i -g @anthropic-ai/claude-code`
- 调用前确认用户同意
- 敏感代码不传给外部模型
