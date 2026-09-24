---
name: riper
description: |
  RIPER workflow core - Research, Innovate, Plan, Execute, Review.
  Five-phase development methodology with verification loops.
  Extended to nine steps for comprehensive project lifecycle.
---

# RIPER Workflow Skill

## Five Phases

| Phase | Focus | Output |
|:---|:---|:---|
| **R**esearch | 理解问题和上下文 | 需求分析文档 |
| **I**nnovate | 探索解决方案 | 技术方案选项 |
| **P**lan | 制定执行计划 | TODO.md + Kanban |
| **E**xecute | 实施开发 | 代码和测试 |
| **R**eview | 审查和验证 | 质量报告 |

## Nine-Step Extension

```
需求创建 → 需求审查 → 方案设计 → 方案审查 
    → 环境搭建 → 开发实施 → 代码提交 → 版本发布 → 完成归档
```

## Phase Protocols

### Research
```yaml
Actions:
  - 检索 knowledge-base
  - 检索 experience
  - 分析现有代码
  - 理解业务需求
Output: .ai_state/requirements/REQ-xxx.md
```

### Plan
```yaml
Actions:
  - 生成 TODO 列表
  - 估算复杂度
  - 识别风险点
  - 规划里程碑
Output: TODO.md, kanban.md
Cunzhi: [PLAN_READY]
```

### Execute
```yaml
Actions:
  - 按 TODO 执行
  - 更新 kanban 状态
  - 验证每个步骤
  - 记录问题
Cunzhi: [PHASE_DONE]
```

### Review
```yaml
Actions:
  - 代码质量检查
  - 测试覆盖验证
  - 安全扫描
  - 经验沉淀
Output: 审查报告
```

## Integration

Works with:
- `phase-router` for workflow selection
- `verification-loop` for quality gates
- `cunzhi` for pause points
