---
name: codex-delegate
description: 调用 Codex CLI 作为子代理
context: fork
allowed-tools:
  - Bash(codex *)
---
## 用途
需要 GPT-5 特定能力、交叉验证、或用户明确要求时

## 调用方式
```bash
codex exec "你的指令"
```

## 规则
- 调用前确认用户同意
- 敏感代码不传给外部模型
- 拿到结果后在当前 agent 验证
