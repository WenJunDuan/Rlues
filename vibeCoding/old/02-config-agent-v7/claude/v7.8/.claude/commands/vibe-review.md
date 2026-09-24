---
name: vibe-review
description: 增强的代码审查，整合规范检索和质量检查
---

# /vibe-review - 增强审查

## Usage

```bash
vibe-review              # 审查当前更改
vibe-review --strict     # 严格模式
vibe-review --security   # 安全审查
```

## Workflow

1. 调用官方 `/review`
2. 加载 knowledge-base (审查规范)
3. 运行 code-quality 检查
4. 执行 verification-loop
5. 生成审查报告
6. 沉淀经验

## Integration

Uses: code-quality, verification-loop, knowledge-base
