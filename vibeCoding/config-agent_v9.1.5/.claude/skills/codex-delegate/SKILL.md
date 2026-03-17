---
name: codex-delegate
description: 将任务委派给 Codex CLI (GPT-5.4) 执行
context: fork
allowed-tools: Bash(codex *)
---
## 何时使用
- 需要 GPT-5.4 模型的特定能力 (数学推理、特定语言生成)
- 需要 "第二意见" 交叉验证当前方案
- 用户明确要求使用 Codex

## 何时不使用
- 当前任务 Claude 完全能胜任 (默认不委派)
- 未确认用户安装了 Codex CLI

## 调用方式
```bash
# 单次任务
codex exec --approval-policy on-request -s workspace-write "$ARGUMENTS"

# 指定模型
codex exec -m gpt-5.4 --approval-policy on-request -s workspace-write "$ARGUMENTS"

# 使用 profile
codex exec --profile review "$ARGUMENTS"

# 只读审查
codex exec -m gpt-5.4 --approval-policy untrusted -s read-only   "Review the following code changes: $(git diff --cached)"
```

## 注意
- 需用户已安装: `npm i -g @openai/codex`
- 调用前确认用户同意委派
- 敏感代码不传给外部模型
