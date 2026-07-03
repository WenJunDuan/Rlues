---
name: cunzhi
description: |
  寸止协议 - Pause and wait mechanism for human confirmation at critical
  decision points. Prevents AI from proceeding autonomously past important
  checkpoints. Core safety and collaboration mechanism.
---

# 寸止 (Cunzhi) Protocol

## Concept

寸止 = "Stop at the inch" - Pause execution at critical points for human review.

## Cunzhi Points

| Point | When | Purpose |
|:---|:---|:---|
| `[REQ_READY]` | 需求分析完成 | 确认理解正确 |
| `[DESIGN_READY]` | 方案设计完成 | 确认技术方案 |
| `[PLAN_READY]` | 计划制定完成 | 确认执行计划 |
| `[PHASE_DONE]` | 阶段执行完成 | 确认继续下一阶段 |
| `[RELEASE_READY]` | 准备发布 | 确认发布 |
| `[TASK_DONE]` | 任务完成 | 确认归档 |

## Invocation

### MCP Tool (Preferred)
```yaml
Tool: mcp-feedback-enhanced
Action: request_confirmation
Message: "[PLAN_READY] 请确认执行计划..."
```

### Fallback
```markdown
---
🛑 **[PLAN_READY]** 寸止等待确认

请审查以上计划，确认后输入:
- `继续` - 执行计划
- `修改` - 调整后重新规划
- `取消` - 终止任务
---
```

## Rules

1. **必须等待** - 不可跳过寸止点
2. **明确输出** - 清晰展示等待内容
3. **选项明确** - 提供清晰的下一步选项
4. **状态保存** - 寸止时保存当前状态

## Integration

Called by:
- `riper` workflow at phase transitions
- `vibe-plan` after planning
- `vibe-review` before commit
