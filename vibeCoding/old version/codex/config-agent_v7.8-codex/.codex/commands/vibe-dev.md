---
name: vibe-dev
description: 智能开发入口。分析用户意图，路由到适当的工作流。
---

# vibe-dev - 智能开发入口

## Usage

```bash
vibe-dev "新功能描述"           # 新建需求
vibe-dev REQ-001               # 继续任务
vibe-dev --path=A "快速修复"   # 指定路径
vibe-dev --engine=claude "任务" # 指定引擎
```

## Workflow

1. **phase-router** 分析意图
2. 路由到对应 **Agent**
3. 加载所需 **Skills**
4. 执行九步工作流
5. 在寸止点等待确认
