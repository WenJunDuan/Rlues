---
name: vibe-review
description: 代码审查，整合规范检索和质量检查
---

# vibe-review - 代码审查

## Usage

```bash
vibe-review              # 审查当前更改
vibe-review --strict     # 严格模式
vibe-review --security   # 安全审查
```

## Workflow

1. 加载 knowledge-base (审查规范)
2. 运行 code-quality 检查
3. 执行 verification-loop
4. 生成审查报告
5. 沉淀经验
