---
name: checkpoint
description: 保存验证检查点
---

# checkpoint - 保存验证状态

## Usage

```bash
checkpoint "auth-complete"      # 创建检查点
checkpoint --list               # 列出检查点
checkpoint --restore "name"     # 恢复检查点
checkpoint --diff "a" "b"       # 比较检查点
```

## Storage

```
.ai_state/checkpoints/
├── checkpoint-001-auth-complete.yaml
└── checkpoint-latest.yaml
```
